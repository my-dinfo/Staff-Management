# Render Deployment Checklist (Myanmar / English)

## Render deployment
1. Put this project in a **private GitHub repository**. Do not commit `.env`, database files, real employee data, or backups.
2. In Render, choose **New + → Blueprint** and connect the repository containing `render.yaml`.
3. Confirm the service uses the included persistent disk mounted at `/var/data`. Persistent disk availability depends on the Render plan. Keep exactly one running instance while using SQLite.
4. Deploy and wait for the `/login` health check to pass.
5. Open `https://YOUR-SERVICE.onrender.com/setup` and create a unique Admin account with a strong password (12+ characters). After the first Admin exists, `/setup` redirects to login.
6. In Admin → Users, create separate accounts for each staff member. Grant Admin only to trusted administrators.
7. Use test records first. Verify user permissions, department filters, Excel (Myanmar/English/Both), PDF (Myanmar/English/Both), backup download, and restore before entering real employee data.
8. Create a backup, download it, and store an encrypted copy outside Render. Test restoration periodically.

## Render environment variables
`render.yaml` sets `SECRET_KEY` using Render-generated secret, `COOKIE_SECURE=1`, `STAFF_DB_PATH=/var/data/staff.db`, and `STAFF_BACKUP_DIR=/var/data/backups`. Do not replace the generated secret with a public or hard-coded value.

## Capacity and limitations
This release uses SQLite on a persistent disk and is designed for one app instance. Thirty-plus registered accounts may be fine for modest office use, but simultaneous write-heavy activity, high availability, or multiple instances requires a PostgreSQL migration and load testing. This code has not yet been migrated to PostgreSQL. The included login throttling is app-level; consider an edge/WAF rate limit too.

## Privacy and security
- Use HTTPS only and unique user accounts.
- Collect only employee information the organization needs and has authority to process.
- Limit Admin accounts and test access permissions.
- Keep encrypted off-site backups; a backup stored only on the same disk is not disaster recovery.
- Review Render access, logs, data region, retention, and applicable privacy requirements.
- Complete an independent security review before using sensitive real employee data.

## PDF Myanmar font note
The project bundles Noto Sans Myanmar font files for PDF output. Check the generated PDF visually after deployment. Complex-script shaping can vary by PDF renderer; if Burmese combining marks are misplaced, switch to a renderer with robust Myanmar shaping before relying on those PDFs as official records.


## အကောင့်ဖွင့်ခြင်းနှင့် Admin ခွင့်ပြုချက်

- အများပြည်သူ/ဝန်ထမ်းများသည် `/signup` မှ Username/Email/Password ဖြင့် အကောင့်ဖွင့်နိုင်သည်။ Google Sign-In ကို ဖွင့်ထားပါက Google Account ဖြင့်လည်း စာရင်းသွင်းနိုင်သည်။
- အသစ်ဖွင့်သမျှအကောင့်များကို `approved=0` အဖြစ်သာ သိမ်းဆည်းသည်။ Admin က `/admin/users` တွင် “ခွင့်ပြုမည်” ကိုနှိပ်မှသာ ဝင်ရောက်ကြည့်ရှုနိုင်သည်။
- ခွင့်မပြုရသေးသူသည် ဝန်ထမ်းစာရင်း၊ ရှာဖွေမှု၊ အစီရင်ခံစာ၊ Export နှင့် Admin စာမျက်နှာများကို မရောက်နိုင်ပါ။ Route အဆင့်တွင်လည်း ခွင့်ပြုချက်စစ်ဆေးထားသည်။
- User Role သည် ကြည့်ရှု/အစီရင်ခံစာထုတ်ယူခွင့်သာရှိသည်။ ဝန်ထမ်းထည့်/ပြင်/ဖျက်နှင့် အလုပ်အကိုင်မှတ်တမ်းပြင်ဆင်ခြင်းကို Admin သာလုပ်နိုင်သည်။
- Google OAuth ဖွင့်ရန် Google Cloud Console တွင် OAuth 2.0 Web Client တစ်ခုဖန်တီးပြီး Authorized Redirect URI ကို `https://YOUR-DOMAIN/auth/google/callback` (LAN အတွက် `http://SERVER-IP:5000/auth/google/callback`) ထည့်ပါ။ `GOOGLE_CLIENT_ID` နှင့် `GOOGLE_CLIENT_SECRET` ကို Environment Variables အဖြစ် ထည့်ပါ။ Google OAuth Client Secret ကို Source Code ထဲ မထည့်ပါနှင့်။
- Google OAuth ကို မသတ်မှတ်ထားလျှင် Google ခလုတ်မပေါ်ဘဲ ပုံမှန် Sign Up အလုပ်လုပ်နေမည်။

အရေးကြီး: ရှိပြီးသား DB အကောင့်များကို schema upgrade က `approved=1` အဖြစ် ဆက်လက်အသုံးပြုနိုင်ရန် ထားသည်။ လက်ရှိအကောင့်အားလုံးကို ပြန်လည်စစ်ဆေးလိုပါက Backup ပြုလုပ်ပြီး Admin DB maintenance ဖြင့် `approved=0` သို့ သတ်မှတ်ပါ။
