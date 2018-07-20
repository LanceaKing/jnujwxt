import os
from urllib.parse import urljoin

heredir = os.path.dirname(os.path.abspath(__file__))


class Config(object):

    JWXT = 'https://jwxt.jnu.edu.cn/'
    JWXT_URLS = {
        'root': JWXT,
        'index': urljoin(JWXT, 'IndexPage.aspx'),
        'login': urljoin(JWXT, 'Login.aspx'),
        'logout': urljoin(JWXT, 'areaTopLogo.aspx'),
        'validcode': urljoin(JWXT, 'ValidateCode.aspx'),
        'xkcenter': urljoin(JWXT, 'Secure/PaiKeXuanKe/wfrm_XK_XuanKe.aspx'),
        'xkrule': urljoin(JWXT, 'Secure/PaiKeXuanKe/wfrm_XK_Rule.aspx'),
        'xkreadme': urljoin(JWXT, 'Secure/PaiKeXuanKe/wfrm_Xk_ReadMeCn.aspx'),
        'search': urljoin(JWXT, 'Secure/PaiKeXuanKe/wfrm_Pk_RlRscx.aspx')
    }
    JWXT_NETS = [
        'http://202.116.0.172:8083/',
        'https://jwxt.jnu.edu.cn/'
    ]
    DATABASE_URI = 'sqlite:///' + os.path.join(heredir, 'jnujwxt.db')
