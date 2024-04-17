# url이 블랙리스트에 있는지 확인하는 코드 필요 -> 이 코드는 학습을 위한 코드이므로 일단 빼둠 마지막에 DB구성 후 추가할 예정
from datetime import datetime
import re
import Levenshtein
from urllib.parse import urlparse
import requests
import ssl
import socket
import whois

trusted_cas = ["GeoTrust", "GoDaddy", "Network Solutions",
               "Thawte", "Comode", "Doster", "VeriSign",
               "Let's Encrypt", "DigiCert", "GlobalSign",
               "Symantec", "RapidSSL", "Entrust", "Comodo CA",
               "Google Trust Services LLC", "Sectigo"]


def is_redirection(url):    # 만약 url이 redirection한다면 redirection하는 url을 반환해서 그 url을 분석
    try:
        response = requests.head(url, allow_redirects=True)
        return response.url
    except:
        return print(f"{url}은 url이 아닙니다.")


def long_url(url):  # url의 길이가 75자 보다 큰 경우 비정상
    if len(url) > 75:
        return 1
    else:
        return 0


def having_ip(url):  # url의 형태가 ip주소 형태인 경우 비정상
    # 000.000.000.000
    pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    pattern += r'|((?:0x[0-9a-fA-F]{1,2}\.){3}0x[0-9a-fA-F]{1,2})'  # 16진수 ip형태
    pattern += r'|(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}'  # ipv6

    if re.match(pattern, url):
        return 1
    else:
        return 0


def having_at(url):  # url에 악의적으로 사용될 가능성이 있는 문자가 사용된 경우 비정상
    if re.search('@', url):
        return 1
    else:
        return 0


def having_dash(url):
    if re.search('-', urlparse(url).netloc):
        return 1
    else:
        return 0


def having_underbar(url):
    if re.search('_', urlparse(url).netloc):
        return 1
    else:
        return 0


def having_redirection(url):
    start = url.find("://") + 3
    url = url[start:]
    url_check = url[start:]
    if re.search('//', url_check):
        return 1
    else:
        return 0


def sub_domains(url):   # url에 .이 5개 이상 있는 경우 비정상
    if url.count(".") > 5:
        return 1
    else:
        return 0


def long_domain(url):  # url의 호스트 이름이 30글자보다 큰 경우 비정상
    domain = urlparse(url).netloc
    if len(domain) > 30:
        return 1
    else:
        return 0


# url의 도메인이 잘 알려진 url의 도메인과 비슷하게 생긴 경우 비정상
def similar_url(url, well_known_domain, threshold=2):
    domain = urlparse(url).netloc
    distance = Levenshtein.distance(domain, well_known_domain)
    if distance <= threshold:
        return 1
    else:
        return 0


def non_standard_port(url):
    parsed_url = urlparse(url)
    port = parsed_url.port
    if port is None:
        return 0
    elif port == 80:    # http 포트
        return 0
    elif port == 443:   # https 포트
        return 0
    else:
        return 1


def is_https(url):
    if urlparse(url).scheme == 'https':
        return 0
    else:
        return 1

# 네트워크가 필요함

# 신뢰받는 인증기관인지, 인증서의 수명도 확인하려했으나 실제로 신뢰받는 사이트의 인증서의 수명이 길지않음 -> 불필요한 것 같음
# 구글, 마이크로소프트, 애플의 인증서의 수명이 1년이 안됨


def is_trusted_cert(url):
    try:
        hostname = urlparse(url).netloc
        context = ssl.create_default_context()
        conn = context.wrap_socket(socket.socket(
            socket.AF_INET), server_hostname=hostname)
        conn.connect((hostname, 443))
        cert = conn.getpeercert()
        issuer = dict(x[0] for x in cert['issuer'])
        issuer_name = issuer.get('organizationName', '')
        print(f"Issuer: {issuer_name}")
        for trusted_ca in trusted_cas:
            if trusted_ca in issuer_name:
                return 0
        return 1
    except Exception as e:
        print(f"Error while checking url {url}: {e}")
        return 1


def get_creation_date(url):
    try:
        domain = whois.whois(url)
        creation_date = domain.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        today = datetime.now()
        age = today - creation_date
    except Exception as e:
        print(f"Error: {e}")
        return 1
    if age.days < 180:
        return 1
    else:
        return 0


def get_expiration_date(url):
    try:
        domain = whois.whois(url)
        expiration_date = domain.expiration_date
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]
        today = datetime.now()
        age = expiration_date - today
        print(age.days)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    if age.days < 365:
        return 1
    else:
        return 0
