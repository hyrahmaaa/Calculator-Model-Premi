import streamlit as st
import math

# --- Fungsi Pembantu (Helper Functions) ---

def combinations(n, k):
    """
    Menghitung kombinasi C(n, k) = n! / (k! * (n-k)!)
    Menggunakan rumus iteratif untuk efisiensi dan menghindari overflow factorial
    untuk n yang besar.
    """
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    # Ambil nilai k yang lebih kecil untuk mengurangi iterasi
    if k > n // 2:
        k = n - k
    
    res = 1
    for i in range(k):
        res = res * (n - i) // (i + 1)
    return res

# --- Fungsi Sesi 1: Menghitung 'a', E[Wt(d,u)], dan STANDAR DEVIASI Wt(d,u) ---

def calculate_a(lambda_val, t_val):
    """
    Menghitung nilai 'a' = exp(-lambda * t).
    """
    return math.exp(-lambda_val * t_val)

def calculate_E_Wt_and_StdDev_Wt(a_val, n, d, u, q, p, alpha_val):
    """
    Menghitung E[Wt(d,u)] dan StdDev[Wt(d,u)] (Standar Deviasi) berdasarkan rumus yang diberikan.
    """
    
    sum_ell_term = 0
    sum_ell_sq_term = 0
    upper_bound_ell = (u - 1) - d

    if upper_bound_ell >= 1:
        for ell in range(1, upper_bound_ell + 1):
            if d + ell > n:
                continue
            binom_val = combinations(n, d + ell)
            term_E = ell * binom_val * (q**(d + ell)) * (p**(n - d - ell))
            sum_ell_term += term_E
            term_Var_sq = (ell**2) * binom_val * (q**(d + ell)) * (p**(n - d - ell))
            sum_ell_sq_term += term_Var_sq

    sum_i_term = 0
    if u <= n:
        for i in range(u, n + 1):
            if i > n:
                continue
            binom_val_i = combinations(n, i)
            term_i = binom_val_i * (q**i) * (p**(n - i))
            sum_i_term += term_i

    E_Wt_d_u = a_val * sum_ell_term + alpha_val * (u - d) * (a_val * sum_i_term + (1 - a_val))

    term_for_E_X_sq = a_val * sum_ell_sq_term + (alpha_val**2) * ((u - d)**2) * (a_val * sum_i_term + (1 - a_val))
    
    true_variance_Wt_d_u = term_for_E_X_sq - (E_Wt_d_u**2)
    
    if true_variance_Wt_d_u < 0:
        st.warning("Peringatan: Variansi (sebelum diakar) yang dihitung negatif. Ini mungkin karena presisi floating point.")
        st.warning("Menggunakan nilai absolut untuk akar kuadrat.")
        std_dev_Wt_d_u = math.sqrt(abs(true_variance_Wt_d_u))
    else:
        std_dev_Wt_d_u = math.sqrt(true_variance_Wt_d_u)
        
    return E_Wt_d_u, std_dev_Wt_d_u

# --- Fungsi Sesi 2: Menghitung P_bar_I ---

def calculate_PI_bar(rho, eta, QT, n, E_Wt_val, StdDev_Wt_val):
    """
    Menghitung P_bar_I berdasarkan E[Wt(d,u)], StdDev[Wt(d,u)], dan parameter lainnya.
    Catatan: StdDev_Wt_val sudah merupakan standar deviasi, jadi tidak perlu diakar lagi.
    """
    denominator = (1 - QT) * n
    
    if denominator == 0:
        return "ERROR: Pembagi (1 - QT) * n tidak boleh nol. Periksa nilai QT dan n."
    
    numerator = (1 + rho + eta) * E_Wt_val + StdDev_Wt_val 
    
    PI_bar = numerator / denominator
    return PI_bar

# --- Fungsi Sesi 3: Menghitung P_TOTAL ---
def calculate_P_TOTAL(PI_bar_val, n_val, P_price):
    """
    Menghitung P_TOTAL = PI_bar * n * P.
    """
    return PI_bar_val * n_val * P_price

# --- Logika Aplikasi Streamlit ---

st.set_page_config(page_title="Kalkulator Asuransi Sapi", layout="centered")

st.title("🐮 Kalkulator Asuransi Sapi Multi-Sesi 🐮")
st.markdown("Aplikasi ini membantu menghitung berbagai metrik asuransi sapi secara bertahap.")

# Inisialisasi session state untuk stage jika belum ada
if 'stage' not in st.session_state:
    st.session_state.stage = 1

# --- Sesi 1: Input dan Output E[Wt] & StdDev[Wt] ---
if st.session_state.stage == 1:
    st.header("Sesi 1: Ekspektasi & Standar Deviasi")
    st.subheader("Input untuk menghitung E[Wt(d,u)] dan StdDev[Wt(d,u)]")

    # Menggunakan kolom untuk tata letak yang lebih rapi
    col1, col2 = st.columns(2)
    with col1:
        lambda_val = st.number_input("Masukkan nilai Lambda (λ):", value=0.01, format="%.6f", key='lambda_s1')
        t_val = st.number_input("Masukkan nilai t:", value=1.0, format="%.2f", key='t_s1')
        n = st.number_input("Masukkan nilai n (jumlah sapi total):", value=100, min_value=1, step=1, key='n_s1')
        d = st.number_input("Masukkan nilai d:", value=5, min_value=0, max_value=n, step=1, key='d_s1')
    with col2:
        u = st.number_input("Masukkan nilai u:", value=10, min_value=0, max_value=n, step=1, key='u_s1')
        q = st.number_input("Masukkan nilai q (probabilitas kematian/kegagalan, 0-1):", value=0.005, min_value=0.0, max_value=1.0, format="%.6f", key='q_s1')
        alpha_val = st.number_input("Masukkan nilai Alpha (α):", value=0.5, format="%.2f", key='alpha_s1')
        # p dihitung otomatis, tidak perlu input

    if st.button("Hitung Sesi 1", key='btn_s1_hitung'):
        # Lakukan validasi
        p = 1 - q # Pastikan p terupdate
        if not (0 <= q <= 1):
            st.error("ERROR: Nilai q harus antara 0 dan 1.")
        elif n <= 0:
            st.error("ERROR: Nilai n harus bilangan bulat positif.")
        elif not (0 <= d <= n and 0 <= u <= n):
            st.error("ERROR: Nilai d dan u harus berada dalam rentang [0, n].")
        else:
            a_calculated = calculate_a(lambda_val, t_val)
            E_Wt_result, StdDev_Wt_result = calculate_E_Wt_and_StdDev_Wt(a_calculated, n, d, u, q, p, alpha_val)

            # Simpan hasil di session_state
            st.session_state.E_Wt_result = E_Wt_result
            st.session_state.StdDev_Wt_result = StdDev_Wt_result
            st.session_state.n_from_stage1 = n # Simpan n juga karena digunakan di Sesi 2 dan 3

            st.subheader("Output Sesi 1:")
            st.info(f"Nilai Ekspektasi (E[Wt(d,u)]): **{E_Wt_result:.8f}**")
            st.info(f"Nilai Standar Deviasi (StdDev[Wt(d,u)]): **{StdDev_Wt_result:.8f}**")
            
            # Pindah ke sesi berikutnya
            st.session_state.stage = 2
            st.rerun() # Memuat ulang aplikasi untuk menampilkan sesi berikutnya

# --- Sesi 2: Input dan Output P_bar_I ---
elif st.session_state.stage == 2:
    st.header("Sesi 2: Perhitungan P_bar_I")
    st.subheader("Input untuk menghitung P_bar_I")
    
    # Tampilkan hasil dari sesi sebelumnya
    st.info(f"E[Wt(d,u)] dari Sesi 1: **{st.session_state.E_Wt_result:.8f}**")
    st.info(f"StdDev[Wt(d,u)] dari Sesi 1: **{st.session_state.StdDev_Wt_result:.8f}**")

    col1, col2 = st.columns(2)
    with col1:
        rho = st.number_input("Masukkan nilai Rho (ρ):", value=0.05, format="%.6f", key='rho_s2')
        eta = st.number_input("Masukkan nilai Eta (η):", value=0.02, format="%.6f", key='eta_s2')
    with col2:
        QT = st.number_input("Masukkan nilai QT:", value=0.1, min_value=0.0, max_value=1.0, format="%.4f", key='qt_s2')

    if st.button("Hitung Sesi 2", key='btn_s2_hitung'):
        if not (0 <= QT <= 1):
            st.error("ERROR: Nilai QT harus antara 0 dan 1.")
        else:
            PI_bar_result = calculate_PI_bar(rho, eta, QT, st.session_state.n_from_stage1, 
                                             st.session_state.E_Wt_result, st.session_state.StdDev_Wt_result)
            
            if isinstance(PI_bar_result, str):
                st.error(PI_bar_result) # Tampilkan pesan error jika ada
            else:
                st.session_state.PI_bar_result = PI_bar_result
                st.subheader("Output Sesi 2:")
                st.success(f"Nilai P_bar_I: **{PI_bar_result:.8f}**")
                st.session_state.stage = 3
                st.rerun()
    
    # Tombol untuk kembali ke sesi sebelumnya (opsional)
    if st.button("Kembali ke Sesi 1", key='btn_s2_back'):
        st.session_state.stage = 1
        st.rerun()


# --- Sesi 3: Input dan Output P_TOTAL ---
elif st.session_state.stage == 3:
    st.header("Sesi 3: Perhitungan P_TOTAL")
    st.subheader("Input untuk menghitung P_TOTAL")

    # Tampilkan hasil dari sesi sebelumnya
    st.success(f"Nilai P_bar_I dari Sesi 2: **{st.session_state.PI_bar_result:.8f}**")

    # Ambil input harga sapi
    P_price = st.number_input("Masukkan nilai P (Harga Sapi):", value=1000000.0, min_value=0.0, format="%.2f", key='p_price_s3')

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Hitung Sesi 3", key='btn_s3_hitung'):
            P_TOTAL_result = calculate_P_TOTAL(st.session_state.PI_bar_result, st.session_state.n_from_stage1, P_price)
            st.subheader("Output Akhir:")
            st.balloons() # Efek visual
            st.success(f"Nilai P_TOTAL: **{P_TOTAL_result:.8f}**")
    with col2:
        if st.button("Mulai Ulang", key='btn_s3_reset'):
            st.session_state.clear() # Hapus semua data sesi
            st.rerun() # Muat ulang aplikasi dari awal
            
    # Tombol untuk kembali ke sesi sebelumnya (opsional)
    if st.button("Kembali ke Sesi 2", key='btn_s3_back'):
        st.session_state.stage = 2
        st.rerun()
