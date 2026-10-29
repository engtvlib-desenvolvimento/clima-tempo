import os
import time
import requests
from datetime import datetime, timezone
from xml.sax.saxutils import escape


API_KEY = "a5facfab4750a52b699065daa2c434f3"
CIDADE = "belem" 
ARQUIVO_XML = r"C:\Users\diagramas\Desktop\Clima tempo\temperatura.xml"

INTERVALO_SEGUNDOS = 300  

INCLUIR_SENSAÇÃO_TERMICA = True
INCLUIR_UMIDADE = True
INCLUIR_DESCRICAO = True

def garantir_pasta_do_arquivo(caminho_arquivo: str) -> None:
    pasta = os.path.dirname(caminho_arquivo)
    if pasta and not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)

def montar_xml(cidade: str, dados: dict) -> str:
    main = dados.get("main", {}) or {}
    weather_list = dados.get("weather", []) or []
    weather0 = weather_list[0] if weather_list else {}

    temp = round(main.get("temp")) if main.get("temp") is not None else None
    feels_like = round(main.get("feels_like")) if main.get("feels_like") is not None else None
    humidity = main.get("humidity")

    descricao = weather0.get("description")

    hora_utc = datetime.now(timezone.utc).isoformat()

    # Segurança: escape em textos
    cidade_xml = escape(str(cidade))

    linhas = []
    linhas.append("<temperatura>")
    linhas.append(f"  <cidade>{cidade_xml}</cidade>")
    linhas.append(f"  <valor>{'' if temp is None else temp}</valor>")
    linhas.append("  <unidade>C</unidade>")
    linhas.append(f"  <hora>{hora_utc}</hora>")

    if INCLUIR_SENSAÇÃO_TERMICA:
        linhas.append(f"  <sensacao>{'' if feels_like is None else feels_like}</sensacao>")

    if INCLUIR_UMIDADE:
        linhas.append(f"  <umidade>{'' if humidity is None else humidity}</umidade>")

    if INCLUIR_DESCRICAO:
        linhas.append(f"  <descricao>{'' if descricao is None else escape(str(descricao))}</descricao>")

    linhas.append("</temperatura>")
    return "\n".join(linhas)

def buscar_temperatura(api_key: str, cidade: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": cidade,
        "units": "metric",
        "lang": "pt_br",
        "appid": api_key
    }
    r = requests.get(url, params=params, timeout=15)
    # Se der erro HTTP (401, 404, etc) levanta exceção
    r.raise_for_status()
    dados = r.json()

    # Algumas falhas retornam JSON com "cod" e "message"
    if isinstance(dados, dict) and str(dados.get("cod", "200")) != "200":
        raise RuntimeError(f"OpenWeather retornou erro: cod={dados.get('cod')} msg={dados.get('message')}")

    return dados

def escrever_arquivo_atomico(caminho: str, conteudo: str) -> None:
    # Escrita atômica: grava em .tmp e depois renomeia (evita vMix ler arquivo pela metade)
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(conteudo)
    os.replace(tmp, caminho)


def main():
    garantir_pasta_do_arquivo(ARQUIVO_XML)

    print("Iniciando gerador de XML de temperatura")
    print("Cidade:", CIDADE)
    print("Destino:", ARQUIVO_XML)
    print("Intervalo (s):", INTERVALO_SEGUNDOS)
    print("-" * 60)

    while True:
        try:
            dados = buscar_temperatura(API_KEY, CIDADE)
            xml = montar_xml(CIDADE, dados)
            escrever_arquivo_atomico(ARQUIVO_XML, xml)

            temp_atual = dados.get("main", {}).get("temp")
            print(f"[OK] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Temp: {temp_atual}°C -> XML atualizado")

        except Exception as e:
            print(f"[ERRO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {e}")

        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    main()
