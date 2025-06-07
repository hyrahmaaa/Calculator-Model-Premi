import streamlit as st
import pandas as pd
import math
import io
from datetime import datetime

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
    
    # Buat container untuk input nama file dan preview
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Input untuk nama file custom
        custom_file_name = st.text_input(
            "Nama file custom (tanpa .csv):",
            value="tabel_probabilitas_Wt",
            help="Masukkan nama file yang Anda inginkan",
            key="custom_filename_input"
        )
    
    with col2:
        # Checkbox untuk menambahkan timestamp
        add_timestamp = st.checkbox(
            "Tambah timestamp", 
            value=False,
            help="Menambahkan tanggal dan waktu pada nama file"
        )
    
    # Validasi dan format nama file
    if custom_file_name.strip():
        # Bersihkan nama file dari karakter yang tidak diizinkan
        clean_filename = "".join(c for c in custom_file_name.strip() if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Tambahkan timestamp jika dipilih
        if add_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"{clean_filename}_{timestamp}.csv"
        else:
            final_filename = f"{clean_filename}.csv"
    else:
        # Nama default jika input kosong
        final_filename = "tabel_probabilitas_Wt.csv"
    
    # Preview nama file yang akan diunduh
    st.info(f"📁 File akan diunduh dengan nama: **{final_filename}**")
    
    # Konversi DataFrame ke CSV
    try:
        # Menggunakan buffer untuk CSV
        csv_buffer = io.StringIO()
        final_table.to_csv(csv_buffer, index=False, float_format='%.6g')
        csv_data = csv_buffer.getvalue()
        
        # Encode to bytes
        csv_bytes = csv_data.encode('utf-8')
        
        # Tombol download dengan nama file yang sudah disiapkan
        st.download_button(
            label="📥 Unduh Tabel CSV",
            data=csv_bytes,
            file_name=final_filename,  # Menggunakan nama file yang sudah diformat
            mime="text/csv",
            type="primary",
            help=f"Klik untuk mengunduh file: {final_filename}",
            key="download_csv_button"  # Key statis untuk menghindari masalah refresh
        )
        
        # Informasi tambahan tentang file
        file_size_kb = len(csv_bytes) / 1024
        st.caption(f"Ukuran file: {file_size_kb:.2f} KB | Format: CSV | Encoding: UTF-8")
        
    except Exception as e:
        st.error(f"Terjadi kesalahan saat menyiapkan file download: {e}")

    # Opsi download format lain
    st.markdown("### Format Download Lainnya")
    
    col_excel, col_json = st.columns(2)
    
    with col_excel:
        # Download sebagai Excel
        try:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                final_table.to_excel(writer, index=False, sheet_name='Probabilitas')
            excel_data = excel_buffer.getvalue()
            
            excel_filename = final_filename.replace('.csv', '.xlsx')
            
            st.download_button(
                label="📊 Unduh sebagai Excel",
                data=excel_data,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_button"
            )
        except Exception as e:
            st.error(f"Error Excel export: {e}")
    
    with col_json:
        # Download sebagai JSON
        try:
            json_data = final_table.to_json(orient='records', indent=2)
            json_filename = final_filename.replace('.csv', '.json')
            
            st.download_button(
                label="📄 Unduh sebagai JSON",
                data=json_data,
                file_name=json_filename,
                mime="application/json",
                key="download_json_button"
            )
        except Exception as e:
            st.error(f"Error JSON export: {e}")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips**: Gunakan nama file yang deskriptif untuk memudahkan identifikasi hasil perhitungan Anda.")
st.sidebar.markdown("Dibuat dengan ❤️ menggunakan Streamlit")
