# jnujwxt default settings
<% import os %>
[jnujwxt]
domain = jwxt.jnu.edu.cn
endpoint = https://jwxt.jnu.edu.cn
basedir = ${basedir}
database_url = sqlite:///${os.path.join('${basedir}', 'db', 'jnujwxt.db')}
endpoint_list = ${os.path.join('${basedir}', 'doc', 'endpoints.txt')}
cookies_path = ${os.path.join('${basedir}', 'doc', 'cookies')}
<%text>
[jnujwxt_url]
login = ${jnujwxt:endpoint}/Login.aspx
logout = ${jnujwxt:endpoint}/areaTopLogo.aspx
validcode = ${jnujwxt:endpoint}/ValidateCode.aspx
xkcenter = ${jnujwxt:endpoint}/Secure/PaiKeXuanKe/wfrm_XK_XuanKe.aspx
xkrule = ${jnujwxt:endpoint}/Secure/PaiKeXuanKe/wfrm_XK_Rule.aspx
xkreadme = ${jnujwxt:endpoint}/Secure/PaiKeXuanKe/wfrm_Xk_ReadMeCn.aspx
search = ${jnujwxt:endpoint}/Secure/PaiKeXuanKe/wfrm_Pk_RlRscx.aspx
</%text>
