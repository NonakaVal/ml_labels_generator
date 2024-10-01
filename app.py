import streamlit as st
import pandas as pd
import os
import io
import requests
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import qrcode
from barcode.codex import Code128
from barcode.writer import ImageWriter
from fpdf import FPDF
import tempfile
import os
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

import tempfile

st.set_page_config(page_title="table-update", page_icon="🦜", layout='wide',initial_sidebar_state=  'collapsed'  )



# st.divider()
# Dicionário de formatos de arquivos suportados
file_formats = {
    "csv": pd.read_csv,
    "xls": pd.read_excel,
    "xlsx": pd.read_excel,
    "xlsm": pd.read_excel,
    "xlsb": pd.read_excel,
}


# def clear_submit():
#     """
#     Limpar o estado do botão de envio
#     """
#     st.session_state["submit"] = False

@st.cache_data(ttl="2h")
def load_data(uploaded_file):
    """
    Carrega o arquivo e retorna um DataFrame do Pandas, com opções específicas para planilhas do Excel.
    """
    try:
        ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
    except:
        ext = uploaded_file.split(".")[-1]
    if ext in file_formats:
        # Adicionando as opções específicas para leitura da planilha
        if ext in ['xls', 'xlsx', 'xlsm', 'xlsb']:
            return pd.read_excel(uploaded_file, sheet_name='Anúncios', header=0, skiprows=[1, 2, 3, 4, 5])
        else:
            return file_formats[ext](uploaded_file)
    else:
        st.error(f"Formato de arquivo não suportado: {ext}")
        return None

# Função para realizar alterações nos dados
def modify_data(df):
    """
    Esta função aplica as alterações necessárias ao DataFrame.
    """
    # Verificar se a coluna 'QR_CODE_LINK' existe, caso contrário preencher com 'N/A'
    qr_code_link = df['QR_CODE_LINK'].fillna('N/A') if 'QR_CODE_LINK' in df.columns else 'N/A'
    
    # Verificar se a coluna 'UNIVERSAL_CODE' existe, caso contrário preencher com 'N/A'
    universal_code = df['UNIVERSAL_CODE'].fillna('N/A') if 'UNIVERSAL_CODE' in df.columns else 'N/A'

    # Verificar se a coluna 'CONDITION' existe, caso contrário preencher com 'N/A'
    condition = df['CONDITION'].fillna('N/A') if 'CONDITION' in df.columns else 'N/A'

    # Criar o novo DataFrame com as colunas desejadas
    new_df = pd.DataFrame({
        'name': df['TITLE'].fillna(method='ffill').shift(1),  # Preencher a coluna 'name' com títulos
        'qr_code_link': qr_code_link,  # Preencher a coluna 'qr_code_link', substituindo valores ausentes
        'price': df['MSHOPS_PRICE'].fillna(method='ffill').shift(1),  # Preencher a coluna 'price'
        'sku': df['SKU'].fillna(method='ffill'),  # Preencher a coluna 'sku', preenchendo valores ausentes com o anterior
        'universal_code': universal_code,  # Preencher a coluna 'universal_code'
        'ad_code': df['ITEM_ID'].fillna(method='bfill').shift(1),  # Preencher a coluna 'ad_code'
        'condition': condition  # Preencher a coluna 'Condition'
    })

    # Remover linhas onde 'price' for 0 ou N/A
    new_df = new_df[new_df['price'] != 0]
    new_df = new_df.dropna(subset=['price', 'name'])

    # Formatar o preço como moeda
    new_df['price'] = new_df['price'].apply(lambda x: f"R$ {x:,.2f}")

    return new_df

# Função para salvar o DataFrame modificado em CSV ou Excel para download
def convert_df(df, ext):
    """
    Converte o DataFrame modificado para o formato especificado (CSV ou Excel) e retorna o buffer.
    """
    buffer = io.BytesIO()
    if ext == "csv":
        df.to_csv(buffer, index=False)
    else:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
    buffer.seek(0)
    return buffer

# Configurações da página


# # st.title("🦜 Gerador de Etiquetas")
# st.markdown("""
# #### ####  Suba e formate a tabela de etiquetas

# """)

st.markdown('####  Tabela de Edição')
# Upload do arquivo
uploaded_file = st.file_uploader(
    "Suba a Planilha de Edição de condições gerais mercado livre, com sku",
    type=list(file_formats.keys()),
    # help="Vários formatos de arquivo são suportados",
    # on_change=clear_submit,
)

# Verificação se o arquivo foi carregado
if uploaded_file:
    ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
    df = load_data(uploaded_file)
    
    if df is not None:
        # st.subheader("Dados Originais")
        #st.dataframe(df, use_container_width=True)
        
        # Realizando alterações nos dados
        df_modified = modify_data(df)
        # st.subheader("Dados Modificados")
        st.data_editor(df_modified)
        
        # Preparando o arquivo modificado para download
        modified_file = convert_df(df_modified, ext)

        # # Botão de download
        # st.download_button(
        #     label="Baixar dados modificados",
        #     data=modified_file,
        #     file_name=f"arquivo_modificado.{ext}",
        #     mime="text/csv" if ext == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        # )
    else:
        st.error("Erro ao carregar o arquivo. Verifique o formato do arquivo.")
# else:
#     st.warning("Por favor, carregue um arquivo para visualizar e modificar os dados.")


tab1, tab2 = st.tabs(["Encurtador de Links", "Gerar PDF"])

with tab1:

    # st.divider()
    # Função para encurtar URL com requests
    def shorten_url_with_requests(url, timeout=10):
        """Encurta uma URL usando o serviço TinyURL com timeout configurável."""
        api_url = f"http://tinyurl.com/api-create.php?url={url}"
        try:
            response = requests.get(api_url, timeout=timeout)
            response.raise_for_status()  # Levanta um erro para respostas de erro HTTP
            return response.text
        except requests.RequestException as e:
            return f"Erro ao encurtar a URL: {str(e)}"

    # # Interface do Streamlit
    # st.title('Gerador de Etiquetas com Encurtador de URL')


    # Formulário para entrada da URL e encurtamento
    # with st.expander("encurtador de links"):
    with st.form("url_shortener_form"):
        url_to_shorten = st.text_input("Insira a URL para encurtar:")
        # timeout = st.slider("Timeout para a requisição (segundos)", min_value=5, max_value=30, value=10)
        shorten_button = st.form_submit_button("Encurtar URL")

    if shorten_button:
        if url_to_shorten:
            # st.info("Encurtando a URL, por favor aguarde...")
            short_url = shorten_url_with_requests(url_to_shorten, timeout=10)
            if short_url.startswith("Erro"):
                st.error(short_url)  # Exibe o erro retornado
            else:
                # st.success(f"URL Encurtada: {short_url}")
                st.markdown(f"""```
                            {short_url}
                            
                            """)  # Link clicável para a URL encurtada
        else:
            st.error("Por favor, insira uma URL válida para encurtar.")


    # st.page_link("pages/Gerar_PDF.py", label="Gerar PDF", icon="📁")
  
 

    class PDF(FPDF):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.add_page()

        def add_label(self, img_buffer, x, y, width, height):
            if self.page_no() == 0:
                self.add_page()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp:
                img_buffer.seek(0)
                temp.write(img_buffer.read())
                temp.flush()
            self.image(temp.name, x, y, width, height)
            os.unlink(temp.name)

    def save_labels_as_pdf(labels):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            pdf = PDF()
            pdf.set_auto_page_break(auto=True, margin=10)
            label_width = 65
            label_height = 45
            labels_per_row = int(210 / label_width)
            labels_per_column = int(297 / label_height)

            for index, label in enumerate(labels):
                if index % (labels_per_row * labels_per_column) == 0 and index != 0:
                    pdf.add_page()

                row = index % labels_per_column
                col = index // labels_per_column

                x = (col % labels_per_row) * label_width
                y = row * label_height

                buffer = BytesIO()
                label.save(buffer, format='PNG')
                pdf.add_label(buffer, x, y, label_width, label_height)

            pdf.output(temp_file.name)
            return temp_file.name  # Retornar o caminho para o arquivo temporário



    # Demais funções de geração de etiquetas e configurações devem ser ajustadas para trabalhar com a nova dimensão


    # Classes e funções fornecidas
    # Custom ImageWriter to remove the numeric text from the barcode
    class CustomImageWriter(ImageWriter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.text = False  # Disable text on barcode

    def generate_barcode(code_text):
        writer = CustomImageWriter()
        code = Code128(code_text, writer=writer)
        buffer = BytesIO()
        code.write(buffer)
        buffer.seek(0)
        return buffer

    def crop_barcode_image(barcode_img, crop_percentage_top=0.1, crop_percentage_bottom=0.4):
        img = Image.open(barcode_img)
        width, height = img.size
        top = int(height * crop_percentage_top)
        bottom = int(height * (1 - crop_percentage_bottom))
        return img.crop((0, top, width, bottom))

    def generate_qr_code(link):
        img = qrcode.make(link)
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        return buffer

    # Função para criar uma única etiqueta
    def create_single_label(name, qr_code_link, price, sku, universal_code, ad_code, condition, config):
        label_width, label_height = 738, 551
        label = Image.new('RGB', (label_width, label_height), 'white')
        draw = ImageDraw.Draw(label)

        fonts = {}
        try:
            fonts['name'] = ImageFont.truetype("arial.ttf", config['name_font_size'])
            fonts['price'] = ImageFont.truetype("arial.ttf", config['price_font_size'])
            fonts['small'] = ImageFont.truetype("arial.ttf", config['small_font_size'])
        except IOError:
            fonts['name'] = ImageFont.load_default()
            fonts['price'] = ImageFont.load_default()
            fonts['small'] = ImageFont.load_default()

        # Adiciona texto
        draw.text((config['name_x'], config['name_y']), name, font=fonts['name'], fill='black')
        
        # Adiciona QR Code
        qr_code_img = Image.open(generate_qr_code(qr_code_link)).resize((config['qr_code_size'], config['qr_code_size']))
        label.paste(qr_code_img, (config['qr_code_x'], config['qr_code_y']))
        
        # Adiciona preço
        draw.text((config['price_x'], config['price_y']), f"{price}", font=fonts['price'], fill='black')

        # Adiciona SKUs e códigos
        text_lines = [
            f"SKU: {sku}",
            f"UN: {universal_code}",
            f"ID: {ad_code}",
            f"{condition}"
        ]
        for i, line in enumerate(text_lines):
            draw.text((config['sku_x'], config['sku_y'] + i * config['sku_spacing']), line, font=fonts['small'], fill='black')

        # Adiciona código de barras
        barcode_img = generate_barcode(sku)
        cropped_barcode_img = crop_barcode_image(barcode_img).resize((config['barcode_width'], config['barcode_height']))
        label.paste(cropped_barcode_img, (config['barcode_x'], label_height - config['barcode_height'] - config['barcode_bottom_padding']))

        
        return label


    # Configuration for label layout
    # Configurações de posição e tamanho
    config = {
        'name_x': 90,
        'name_y': 110,
        'qr_code_x': 60,
        'qr_code_y': 160,
        'qr_code_size': 260,
        'price_x': 320,
        'price_y': 190,
        'sku_x': 320,
        'sku_y': 240,
        'sku_spacing': 45,
        'barcode_x': 50,
        'barcode_width': 600,
        'barcode_height': 80,
        'barcode_bottom_padding': 20,
        'name_font_size': 19,
        'price_font_size': 35,
        'small_font_size': 30,
        'margin_top': 80,
        'margin_bottom': 80,
        'margin_left': 40,
        'margin_right': 15,
        'spacing_horizontal': 90,
        'spacing_vertical': 10
    }


with tab2:
  
    st.markdown(
        'Baixe a tabela com o botão de download e carregue o arquivo csv.'

    )


    def create_labels_from_excel(file_path, config):
        df = pd.read_csv(file_path)
        print("DataFrame Loaded. Columns:", df.columns)  # Verificar as colunas do DataFrame
        labels = []
        for index, row in df.iterrows():
            # Atualizar para usar os nomes das colunas corretos
            name = row.get('name', '')  # Nome da coluna ajustado
            qr_code_link = row.get('qr_code_link', '')  # Nome da coluna ajustado
            price = row.get('price', '')  # Nome da coluna ajustado
            sku = row.get('sku', '')  # Nome da coluna ajustado
            universal_code = row.get('universal_code', '')  # Nome da coluna ajustado
            ad_code = row.get('ad_code', '')  # Nome da coluna ajustado
            condition = row.get('condition', '')  # Nome da coluna ajustado

            print(f"Processing row {index}: {name}, {qr_code_link}, {price}, {sku}, {universal_code}, {ad_code}, {condition}")

            label_image = create_single_label(name, qr_code_link, price, sku, universal_code, ad_code, condition, config)
            labels.append(label_image)

        return labels
    uploaded_file = st.file_uploader("Carregue o arquivo CSV", type=["csv"])

    if uploaded_file is not None:
        try:
            with st.spinner("Gerando etiquetas..."):
                labels = create_labels_from_excel(uploaded_file, config)  # Atualizar para ler CSV
                if labels:
                    pdf_path = save_labels_as_pdf(labels)  # Salvar etiquetas como PDF temporariamente
                    st.success("Etiquetas geradas com sucesso e salvas como PDF!")
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="Baixar PDF de Etiquetas",
                            data=pdf_file.read(),
                            file_name="etiquetas.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.warning("Nenhuma etiqueta foi gerada. Verifique os dados de entrada.")
        except Exception as e:
            st.error(f"Ocorreu um erro: {str(e)}")
    else:
        st.info("Carregue um arquivo para começar a gerar etiquetas.")



    # uploaded_file = st.file_uploader("Carregue o arquivo csv", type=["csv"])





