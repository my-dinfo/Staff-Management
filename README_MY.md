# ဝန်ထမ်းအင်အား စီမံခန့်ခွဲမှု Web App (Cloud-ready Starter)

ပါဝင်သည်: Login, Admin/User roles, employee profiles, employment history, SQLite persistence, မြန်မာ/English Excel/PDF export, department report, database backup/restore, audit log, login attempt throttling, security response headers.

## 1. Local Windows testing
1. Python 3.10+ install လုပ်ပါ။
2. Project folder ထဲ Command Prompt ဖွင့်ပါ။
3. Run:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
4. Browser မှ `http://127.0.0.1:5000/setup` ဖွင့်ပါ။
5. ပထမဆုံး Admin username နှင့် အနည်းဆုံး 12 လုံး password ဖန်တီးပါ။
6. Login ဝင်ပြီး ဝန်ထမ်းစာရင်း စတင်ထည့်ပါ။

## 2. Public internet deployment (Render example)
- GitHub account ထဲ private repository တစ်ခုဖန်တီးပြီး project files upload/push လုပ်ပါ။
- Render တွင် New Blueprint သို့မဟုတ် Web Service ကိုရွေးပြီး repository ချိတ်ပါ။
- `render.yaml` သည် Waitress production server (threads=8), `/login` health check, HTTPS secure cookie setting, generated SECRET_KEY နှင့် persistent disk path များကို သတ်မှတ်ထားသည်။ Persistent disk ရရှိနိုင်မှုသည် Render plan ပေါ်မူတည်နိုင်သည်။
- Deploy ပြီး URL ရလာပါက `/setup` သို့သွားပြီး ပထမဆုံး Admin ကို ဖန်တီးပါ။
- Persistent disk ကို hosting provider က plan/region အလိုက် support လုပ်ကြောင်း စစ်ပါ။ SQLite ကို app instance အများအပြားတွင် တစ်ပြိုင်နက် share မလုပ်ပါနှင့်။ Multi-instance သို့မဟုတ် concurrent heavy usage အတွက် PostgreSQL ကို သုံးပါ။
- မိမိ hosting provider ၏ current pricing, persistent storage, backup/restore, HTTPS နှင့် region/privacy settings ကို deploy မလုပ်မီ စစ်ဆေးပါ။

## 3. Reports in Myanmar and English
- Reports စာမျက်နှာတွင် Excel/PDF အတွက် `မြန်မာ`, `English`, `နှစ်ဘာသာ / Both` ကိုရွေးနိုင်သည်။
- Excel နှစ်ဘာသာမုဒ်တွင် column headings နှစ်ဘာသာပါဝင်သည်။ English-only mode တွင် ဌာနနှင့် အလုပ်အခြေအနေများကို English label သို့ ပြောင်းပေးသည်။
- PDF တွင် Noto Sans Myanmar font ကို project ထဲ ထည့်ထားသည်။ ReportLab ၏ complex-script shaping အကန့်အသတ်ကြောင့် မြန်မာစာအမှတ်အသားနေရာချထားမှုကို live deployment မှာ စမ်းသပ်ပါ။ မှန်ကန်မှုမရှိပါက Unicode shaping ကို ထောက်ပံ့သော PDF renderer သို့ ပြောင်းရန်လိုနိုင်သည်။

## 4. Security before real office use
- Production `SECRET_KEY` ကို environment variable ဖြင့် သတ်မှတ်ပါ; source code ထဲ မထည့်ပါနှင့်။
- HTTPS သာအသုံးပြုပါ (`COOKIE_SECURE=1`).
- Admin password ကို မျှဝေမထားပါနှင့်; unique user accounts ပေးပါ; password manager သုံးပါ။
- အနည်းဆုံး 12+ character password, အကောင့်မလိုတော့လျှင် deactivate, admin access အနည်းဆုံးထားပါ။
- ဝန်ထမ်း၏ မွေးသက္ကရာဇ်၊ လိပ်စာ၊ အရေးပေါ်ဆက်သွယ်ရန်တို့သည် sensitive personal data ဖြစ်နိုင်သည်။ လိုအပ်သလောက်သာ သိမ်းပါ၊ ခွင့်ပြုထားသူများသာ ဝင်ကြည့်စေပါ။
- Backups များကို encrypted storage/private location ထဲသိမ်းပါ။ ပုံမှန် restore test လုပ်ပါ။
- Hosting မှာ automated backups, log monitoring, OS/package patching, incident-response contact တို့ကို စီစဉ်ပါ။
- PDF export တွင် အင်္ဂလိပ်/Latin font ဖြင့် report ကို ထုတ်ပေးထားသည်။ မြန်မာစာ PDF လိုအပ်ပါက သင့်တော်သော Unicode Myanmar font (ဥပမာ Noto Sans Myanmar) ကို license/embedding terms စစ်ဆေးပြီး server တွင် ထည့်သွင်း configure လုပ်ရန် လိုအပ်နိုင်သည်။
- Audit log table ရှိပြီး အရေးကြီးသော login/CRUD/export/backup actions များကို မှတ်တမ်းတင်သည်။ ဤ starter UI တွင် audit log viewer မပါသေးပါ။
- This starter has no rate limiting, MFA, formal password reset email, or independent security audit. Internet exposure မလုပ်မီ IT/security review ပြုလုပ်ပါ။

## 5. Database and backups
- Database default path: `data/staff.db`
- Backup default path: `backups/`
- Admin > Backup မှ backup create/download/restore လုပ်နိုင်သည်။
- Restore သည် database content ကို အစားထိုးမည်။ Restore မတိုင်မီ လက်ရှိ database ကို backup လုပ်ပါ; restore ပြီးနောက် re-login လုပ်ပါ။
- Cloud instance ပျက်သွားလျှင် local SQLite file သာရှိပြီး persistent disk မရှိပါက data ပျောက်နိုင်သည်။ Persistent volume နှင့် off-site encrypted backups မဖြစ်မနေ စီစဉ်ပါ။

## 6. Permissions
- Admin: user management, backup/restore, employee delete, all reports.
- User: login, view/create/edit employee data, add employment history, export reports.
- User can view and edit personal employee records across the system in this starter. If that is too broad, implement department-scoped authorization before deployment.

## 7. Known limitations / next production steps
- PDF report uses standard reportlab font; Burmese glyph support may need a Unicode Myanmar TTF font configured on server.
- SQLite is appropriate for a small single-instance office app; for larger concurrent teams, migrate to PostgreSQL.
- Add rate limiting, MFA, password reset workflow, audit log viewer, automated backup schedule, privacy/retention policy, and security test before production.


## Render deployment checklist (before go-live)
1. GitHub တွင် **private** repository ဖန်တီးပြီး project source code တင်ပါ။ `.env` သို့မဟုတ် database backup ဖိုင်များကို မတင်ပါနှင့်။
2. Render Dashboard → **New + → Blueprint** → repository ကိုချိတ်ဆက်ပြီး `render.yaml` ကိုအသုံးပြုပါ။
3. Persistent Disk ကို service တွင် mount လုပ်နိုင်သော plan ကိုရွေးပါ။ SQLite database path `/var/data/staff.db` ဖြစ်ပြီး app instance တစ်ခုတည်းသာ အသုံးပြုပါ။ Scale to multiple instances မလုပ်ပါနှင့်။
4. Deploy အောင်မြင်ပြီးနောက် `https://<your-service>.onrender.com/setup` ကိုဖွင့်၍ ပထမဆုံး Admin ကိုဖန်တီးပါ။ Admin account ကို အခြားသူနှင့် မမျှဝေပါနှင့်။
5. Admin မှ user account တစ်ခုချင်းစီဖန်တီးပါ။ ဝန်ထမ်းအချက်အလက်အစစ်များမထည့်မီ dummy data ဖြင့် Login, permissions, Excel/PDF မြန်မာ/English, backup/download/restore ကို စမ်းသပ်ပါ။
6. Render logs နှင့် health check ကို စစ်ပါ။ Persistent Disk မရှိပါက redeploy/restart ပြီး data ပျောက်နိုင်သည်။ Backup များကို App disk တစ်ခုတည်းတွင်သာ မထားဘဲ encrypted off-site storage သို့ ပုံမှန်ကူးပါ။
7. **30+ accounts** အတွက် single-instance SQLite သည် low/moderate traffic ဖြင့် စတင်အသုံးပြုနိုင်သော်လည်း simultaneous write load နှင့် high availability လိုအပ်ပါက PostgreSQL migration ကို deployment မတိုင်မီ စီစဉ်ပါ။ လက်ရှိ code သည် PostgreSQL-ready မဟုတ်သေးပါ။

## 8. ရုံးအတွင်း ကွန်ပျူတာအများအပြား (LAN)

ရုံးအတွင်း PC များစွာမှ တစ်ပြိုင်နက်အသုံးပြုရန် `INSTALL_OFFICE_LAN_MY.md` ကို ဖတ်ပါ။ Server PC တစ်လုံးတွင် `install_office_server.bat` ကို တစ်ကြိမ် run ပြီး `start_office_server.bat` ဖြင့် App ကိုဖွင့်ပါ။ Client PC များက `http://SERVER-IP:5000` ကို Browser မှ ဝင်ပါ။ Database ကို Server PC တစ်လုံးထဲတွင်သာထားပါ။

Reports စာမျက်နှာတွင် ဌာနတစ်ခုရွေးပြီး Excel/PDF ကို မြန်မာ၊ English သို့မဟုတ် နှစ်ဘာသာဖြင့် ထုတ်ယူနိုင်သည်။

**မှတ်ချက်:** 30+ account များအတွက် single-server SQLite သည် စတင်အသုံးပြုနိုင်သော်လည်း တစ်ပြိုင်နက် write traffic များလျှင် PostgreSQL သို့ migration လုပ်ရန် လိုအပ်သည်။ LAN HTTP သည် encrypted မဟုတ်သောကြောင့် ဝန်ထမ်းကိုယ်ရေးအချက်အလက်များအတွက် internal HTTPS သို့မဟုတ် VPN ကို စီစဉ်ပါ။


## အကောင့်ဖွင့်ခြင်းနှင့် Admin ခွင့်ပြုချက်

- အများပြည်သူ/ဝန်ထမ်းများသည် `/signup` မှ Username/Email/Password ဖြင့် အကောင့်ဖွင့်နိုင်သည်။ Google Sign-In ကို ဖွင့်ထားပါက Google Account ဖြင့်လည်း စာရင်းသွင်းနိုင်သည်။
- အသစ်ဖွင့်သမျှအကောင့်များကို `approved=0` အဖြစ်သာ သိမ်းဆည်းသည်။ Admin က `/admin/users` တွင် “ခွင့်ပြုမည်” ကိုနှိပ်မှသာ ဝင်ရောက်ကြည့်ရှုနိုင်သည်။
- ခွင့်မပြုရသေးသူသည် ဝန်ထမ်းစာရင်း၊ ရှာဖွေမှု၊ အစီရင်ခံစာ၊ Export နှင့် Admin စာမျက်နှာများကို မရောက်နိုင်ပါ။ Route အဆင့်တွင်လည်း ခွင့်ပြုချက်စစ်ဆေးထားသည်။
- User Role သည် ကြည့်ရှု/အစီရင်ခံစာထုတ်ယူခွင့်သာရှိသည်။ ဝန်ထမ်းထည့်/ပြင်/ဖျက်နှင့် အလုပ်အကိုင်မှတ်တမ်းပြင်ဆင်ခြင်းကို Admin သာလုပ်နိုင်သည်။
- Google OAuth ဖွင့်ရန် Google Cloud Console တွင် OAuth 2.0 Web Client တစ်ခုဖန်တီးပြီး Authorized Redirect URI ကို `https://YOUR-DOMAIN/auth/google/callback` (LAN အတွက် `http://SERVER-IP:5000/auth/google/callback`) ထည့်ပါ။ `GOOGLE_CLIENT_ID` နှင့် `GOOGLE_CLIENT_SECRET` ကို Environment Variables အဖြစ် ထည့်ပါ။ Google OAuth Client Secret ကို Source Code ထဲ မထည့်ပါနှင့်။
- Google OAuth ကို မသတ်မှတ်ထားလျှင် Google ခလုတ်မပေါ်ဘဲ ပုံမှန် Sign Up အလုပ်လုပ်နေမည်။

အရေးကြီး: ရှိပြီးသား DB အကောင့်များကို schema upgrade က `approved=1` အဖြစ် ဆက်လက်အသုံးပြုနိုင်ရန် ထားသည်။ လက်ရှိအကောင့်အားလုံးကို ပြန်လည်စစ်ဆေးလိုပါက Backup ပြုလုပ်ပြီး Admin DB maintenance ဖြင့် `approved=0` သို့ သတ်မှတ်ပါ။


Google Login သတိပြုရန်: Google OAuth သည် လုံခြုံသော HTTPS callback လိုအပ်သည် (localhost exception မှလွဲ၍)။ LAN IP ဖြင့် `http://192.168.x.x:5000/auth/google/callback` သည် Google OAuth တွင် ပုံမှန်အားဖြင့် လက်မခံနိုင်ပါ။ Google Login သုံးလိုပါက ရုံး၏ internal DNS/domain နှင့် trusted HTTPS certificate သတ်မှတ်ပါ။ မသတ်မှတ်နိုင်သေးလျှင် `/signup` ဖြင့် Local Account ဖွင့်ပြီး Admin ခွင့်ပြုချက်စနစ်ကို အသုံးပြုနိုင်ပါသည်။
