import streamlit as st
import pandas as pd
import math
import io

# --- Inisialisasi st.session_state ---
if 'calculated_data' not in st.session_state:
    st.session_state['calculated_data'] = {'table': pd.DataFrame(), 'params': {}}

# --- Fungsi Perhitungan Inti (Tidak Berubah) ---
def calculate_pr_Wt_k_for_single_lambda(n, q, lambda_val, t_val):
    p = 1 - q
    probabilities = []

    try:
        exp_lambda_t = math.exp(-lambda_val * t_val)
    except OverflowError:
        st.warning(f"Peringatan: Nilai lambda * t ({lambda_val * t_val}) terlalu besar, menyebabkan OverflowError untuk e^(-lambda * t). Mengembalikan probabilitas 0.")
        return [0.0] * (n + 1)
    except Exception as e:
        st.error(f"Error saat menghitung e^(-lambda * t) untuk lambda={lambda_val}, t={t_val}: {e}")
        return [0.0] * (n + 1)

    for k in range(n + 1):
        if k < n:
            binomial_coefficient = math.comb(n, k)
            prob_k = binomial_coefficient * (q**k) * (p**(n - k)) * exp_lambda_t
        else: # k == n
            prob_k = (q**n * exp_lambda_t) + (1 - exp_lambda_t)
        
        probabilities.append(prob_k)
        
    return probabilities

def generate_probability_table(n, q, t, lambda_values_dict):
    if not (isinstance(n, int) and n >= 0) or not (0 <= q <= 1) or t < 0:
        return pd.DataFrame() 
    
    df = pd.DataFrame({'k': list(range(n + 1))})

    for lambda_str_name, lambda_val in lambda_values_dict.items():
        if lambda_val < 0:
            st.warning(f"Peringatan: Nilai lambda '{lambda_str_name}' adalah negatif. Kolom ini akan diisi nol.")
            df[lambda_str_name] = [0.0] * (n + 1)
            continue

        probs_for_lambda = calculate_pr_Wt_k_for_single_lambda(n, q, lambda_val, t)
        df[lambda_str_name] = probs_for_lambda
    
    return df

# --- Bagian UI Streamlit ---

st.set_page_config(
    page_title="Kalkulator Pr{Wt = k} (Distribusi Modifikasi)",
    page_icon="🧮",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🧮 Kalkulator Probabilitas Wt")

st.markdown(
    """
    Aplikasi ini menghitung probabilitas $Pr\\{W_t = k\\}$ berdasarkan formula:

    $$
    Pr\\{W_t = k\\} =
    \\begin{cases}
        \\binom{n}{k} q^k p^{n-k} a, & k = 0, 1, 2, \\dots, (n-1) \\\\
        q^n a + (1-a), & k = n.
    \\end{cases}
    $$
    dengan $q = 1 - p$ dan $a = (e^{-\\lambda t})$
    """
)

st.sidebar.header("Input Parameter")

# Input widget untuk n
n_input = st.sidebar.number_input(
    "Masukkan nilai n (jumlah maksimum k, bilangan bulat non-negatif):",
    min_value=0,
    step=1,
    value=10, # Default value
    key="n_input"
)

# Input widget untuk q
q_input = st.sidebar.number_input(
    "Masukkan nilai q (probabilitas kegagalan, antara 0 dan 1):",
    min_value=0.0,
    max_value=1.0,
    step=0.01,
    value=0.2, # Default value
    format="%.2f",
    key="q_input"
)

# Input widget untuk t
t_input = st.sidebar.number_input(
    "Masukkan nilai t (waktu dalam tahun, non-negatif):",
    min_value=0.0,
    step=0.1,
    value=1.0, # Default value
    format="%.2f",
    key="t_input"
)

# Input widget untuk nilai-nilai lambda (dipisahkan koma)
lambda_input_str = st.sidebar.text_input(
    "Masukkan variasi nilai lambda yang dipisahkan koma, contoh: 0.000696,0.000325):",
    value="0.000696,0.000325,0.000128,0.000173", # Default values dari gambar
    key="lambda_str_input"
)

# Tombol untuk memicu perhitungan
if st.sidebar.button("Hitung Probabilitas"):
    # Validasi Input
    if n_input < 0:
        st.error("Nilai 'n' harus bilangan bulat non-negatif.")
        st.session_state['calculated_data'] = {'table': pd.DataFrame(), 'params': {}}
        st.stop()
    if not (0 <= q_input <= 1):
        st.error("Nilai 'q' harus antara 0 dan 1.")
        st.session_state['calculated_data'] = {'table': pd.DataFrame(), 'params': {}}
        st.stop()
    if t_input < 0:
        st.error("Nilai 't' harus non-negatif.")
        st.session_state['calculated_data'] = {'table': pd.DataFrame(), 'params': {}}
        st.stop()

    # Parse string lambda menjadi dictionary
    lambda_data = {}
    parsed_lambdas = []
    if lambda_input_str:
        for item in lambda_input_str.split(','):
            try:
                val = float(item.strip())
                parsed_lambdas.append(val)
                lambda_data[item.strip()] = val # Key adalah string dari nilai lambda
            except ValueError:
                st.error(f"Nilai lambda '{item.strip()}' tidak valid. Harap masukkan angka yang dipisahkan koma.")
                st.session_state['calculated_data'] = {'table': pd.DataFrame(), 'params': {}}
                st.stop()

    if not parsed_lambdas:
        st.warning("Tidak ada nilai lambda yang dimasukkan. Tidak ada tabel yang akan dibuat.")
        st.session_state['calculated_data'] = {'table': pd.DataFrame(), 'params': {}}
    else:
        try:
            temp_final_table = generate_probability_table(n_input, q_input, t_input, lambda_data)
            
            st.session_state['calculated_data'] = {
                'table': temp_final_table,
                'params': {'n': n_input, 'q': q_input, 't': t_input, 'lambdas_str': lambda_input_str}
            }
        except Exception as e:
            st.error(f"Terjadi kesalahan saat menghitung: {e}")
            st.info("Pastikan input Anda valid dan coba lagi.")
            st.session_state['calculated_data'] = {'table': pd.DataFrame(), 'params': {}}

# --- Bagian Tampilan Hasil dan Unduh ---
if not st.session_state['calculated_data']['table'].empty:
    final_table = st.session_state['calculated_data']['table']
    table_params = st.session_state['calculated_data']['params']

    st.subheader("Hasil Perhitungan")
    st.write(f"Parameter: n={table_params['n']}, q={table_params['q']}, t={table_params['t']}")

    # Tampilkan tabel dengan pemformatan 6 digit signifikan / E-notation
    st.dataframe(final_table.style.format('{:.6g}'))

    # Cek Total Probabilitas per Kolom
    st.markdown("---")
    st.markdown("**Total Probabilitas (Per Kolom Lambda):**")
    total_probs_series = final_table.drop(columns=['k']).sum()
    st.dataframe(total_probs_series.to_frame().T.style.format('{:.6g}'))

    # Peringatan jika total tidak 1.0
    for col, total in total_probs_series.items():
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            st.warning(
                f"⚠️ Peringatan untuk kolom '{col}': Total probabilitas tidak mendekati 1.0 ({total:.10f}). "
                "Ini mungkin disebabkan oleh pembulatan atau sifat khusus dari formula distribusi."
            )
        else:
            st.success(f"🎉 Kolom '{col}': Total probabilitas mendekati 1.0 ({total:.10f}).")

    # --- Fitur Rename File dan Unduh Tabel ---
    st.markdown("---")
    st.subheader("Unduh Tabel Hasil")
    
    # Nama file default yang sederhana dan statis
    base_default_name = "tabel_probabilitas_Wt" 

    # Input untuk nama file. Nilai defaultnya adalah nama statis dasar
    custom_file_name_base = st.text_input(
        "Masukkan nama file untuk diunduh (tanpa ekstensi .csv):",
        value=base_default_name,
        key="download_file_name_input_static"
    )
    
    # Pastikan nama file tidak kosong dan tambahkan ekstensi .csv jika belum ada
    if custom_file_name_base.strip() == "":
        final_download_name = base_default_name + ".csv" 
    elif not custom_file_name_base.strip().endswith(".csv"):
        final_download_name = custom_file_name_base.strip() + ".csv"
    else:
        final_download_name = custom_file_name_base.strip()

    # (Opsional) Baris debug untuk melihat nama file akhir
    # st.info(f"Nama file yang akan diunduh: {final_download_name}")

    # Konversi DataFrame ke string CSV
    csv_string_io = io.StringIO()
    final_table.to_csv(csv_string_io, index=False, float_format='%.6g')
    csv_bytes = csv_string_io.getvalue().encode('utf-8')

    # Tombol Unduh
    # Key dibuat dinamis berdasarkan final_download_name agar Streamlit merefresh tombol
    # saat nama file berubah, mengatasi masalah cache.
    st.download_button(
        label="Unduh Tabel sebagai CSV",
        data=csv_bytes,
        file_name=final_download_name,
        mime="text/csv",
        key=f"download_button_{final_download_name}" # KEY DINAMIS DITAMBAHKAN DI SINI
    )

st.sidebar.markdown("---")
st.sidebar.info("Dibuat dengan Streamlit")
