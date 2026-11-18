# ရုံးအတွင်း ကွန်ပျူတာအများအပြားဖြင့် အသုံးပြုရန် (LAN Installation)

## အကြံပြုထားသော ချိတ်ဆက်ပုံ

- Server PC တစ်လုံးကို အမြဲဖွင့်ထားပါ။ App နှင့် Database သည် ထိုစက်တစ်လုံးထဲတွင်သာ ရှိရမည်။
- အခြားရုံးကွန်ပျူတာများသည် Chrome/Edge Browser မှ Server PC ၏ IP နှင့် Port `5000` ကို အသုံးပြုမည်။
- Client PC များတွင် Python သို့မဟုတ် Database သီးခြားတပ်ဆင်ရန် မလိုပါ။
- Database ဖိုင် `data/staff.db` ကို Network Share ထဲမထားပါနှင့်။ Server PC ၏ Local Disk ထဲတွင်သာထားပါ။

## Server PC လိုအပ်ချက်

- Windows 10/11 64-bit၊ Python 3.10+၊ RAM 8 GB အကြံပြု၊ SSD နှင့် ပုံမှန် backup လုပ်နိုင်သော disk။
- Server PC ကို UPS ဖြင့် ကာကွယ်ရန်၊ Sleep mode ပိတ်ရန်၊ Windows Update ကို စီစဉ်ရန် အကြံပြုသည်။
- Server PC ကို ရုံး LAN ထဲတွင် Static IP သို့မဟုတ် DHCP Reservation သတ်မှတ်ပါ။ ဥပမာ `192.168.1.50`။ မိမိရုံး Network Admin နှင့် IP မတိုက်မိကြောင်း စစ်ဆေးပါ။

## တပ်ဆင်ခြင်း

1. ZIP ဖိုင်ကို Server PC တွင် Extract လုပ်ပါ။
2. Python 3.10+ ကို install လုပ်ပါ။ Python installer တွင် `Add Python to PATH` ကို ရွေးပါ။
3. Project folder ထဲမှ `install_office_server.bat` ကို Run လုပ်ပါ။ လိုအပ်သော Python packages များ install လုပ်မည်။
4. `start_office_server.bat` ကို Run လုပ်ပါ။ Command window ကို မပိတ်ပါနှင့်။
5. Server PC ပေါ် Browser မှ `http://127.0.0.1:5000/setup` ကို ဖွင့်ပါ။ ပထမဆုံး Admin အကောင့်ကို ဖန်တီးပါ။ Password ကို အနည်းဆုံး 12 လုံးထားပါ။
6. Server PC ၏ LAN IP ကို စစ်ရန် Command Prompt တွင် `ipconfig` ရိုက်ပြီး IPv4 Address ကို မှတ်ပါ။
7. အခြား PC များတွင် `http://192.168.1.50:5000` ကို ဖွင့်ပါ။ အထက်ပါ IP ကို မိမိ Server IP ဖြင့် အစားထိုးပါ။
8. Admin မှာ ဝန်ထမ်းတစ်ဦးစီအတွက် User account သီးခြားဖန်တီးပါ။ Admin password မျှဝေမသုံးပါနှင့်။

## Windows Firewall

- Windows Defender Firewall တွင် TCP Port `5000` ကို **Private network profile** အတွက်သာ inbound ခွင့်ပြုပါ။
- Domain/Private profile များကို IT Admin က စစ်ဆေးပြီး လိုအပ်သည့် ရုံး LAN subnet မှသာ ခွင့်ပြုပါ။
- Public profile အတွက် မဖွင့်ပါနှင့်။ Router တွင် Port Forwarding မလုပ်ပါနှင့်။ Internet မှ အဝေးကနေ ဝင်ရန် လိုအပ်ပါက VPN သို့မဟုတ် လုံခြုံသော HTTPS Cloud deployment ကို သုံးပါ။
- LAN HTTP သည် Network အတွင်း traffic encryption မပေးပါ။ ဝန်ထမ်းကိုယ်ရေးအချက်အလက်များအတွက် internal HTTPS reverse proxy သို့မဟုတ် managed VPN ကို စီစဉ်ရန် အကြံပြုသည်။

## Backup နှင့် Restore

- Admin account ဖြင့် ဝင်ပြီး `Backup` စာမျက်နှာမှ Backup ဖန်တီးပါ။
- Backup ဖိုင်များသည် `backups/` ထဲတွင် ရှိမည်။ တခြား encrypted external drive သို့မဟုတ် access ကန့်သတ်ထားသော backup storage သို့ ပုံမှန်ကူးပါ။
- Backup ဖိုင်များကို Email/Chat မှတဆင့် မပို့ပါနှင့်။
- Restore သည် လက်ရှိ Database ကို အစားထိုးမည်။ Restore မလုပ်မီ လက်ရှိအခြေအနေ Backup ကို အရင်လုပ်ပါ။ Restore ပြီးလျှင် login ပြန်ဝင်ပြီး ဝန်ထမ်းစာရင်း၊ user account နှင့် report များကို စစ်ဆေးပါ။
- အနည်းဆုံး တစ်လတစ်ကြိမ် Restore စမ်းသပ်ပါ။ Backup ရှိရုံဖြင့် Restore အောင်မြင်မည်ဟု မယူဆပါနှင့်။

## အသုံးပြုသူ 30+ ဦးအတွက် လုပ်ငန်းလည်ပတ်မှု

- App ကို Server PC တစ်လုံးတည်းတွင်သာ run ပါ။ `data/staff.db` ကို Client PC များထံ မကူးပါနှင့်။
- SQLite သည် ရုံးတွင်းအသုံးပြုမှုအလယ်အလတ်အတွက် single-server စနစ်ဖြင့် စတင်နိုင်သော်လည်း တစ်ပြိုင်နက်ရေးသားမှုများသောအခါ database lock/response နှေးခြင်း ဖြစ်နိုင်သည်။
- တစ်ပြိုင်နက်တည်း အသုံးပြုသူများစွာက စာရင်းများကို မကြာခဏ ပြင်ဆင်ရမည်၊ သို့မဟုတ် အဝေးမှလည်း အသုံးပြုမည်ဆိုပါက PostgreSQL သို့ ပြောင်းရွှေ့ပြီး App ကို HTTPS Cloud/VPN ပေါ်တွင် တင်ရန် လိုအပ်သည်။ လက်ရှိ code သည် SQLite သုံးထားပြီး PostgreSQL migration မပါသေးပါ။
- Server PC ပိတ်သွားလျှင် အခြားကွန်ပျူတာများက App ကို ဝင်မရပါ။ Server PC ကို အမြဲဖွင့်ထားရန် လိုအပ်သည်။

## လုံခြုံရေးစည်းမျဉ်း

- User တစ်ဦးလျှင် account တစ်ခုစီသာ သုံးပါ။ ဝန်ထမ်းအလုပ်ထွက်/တာဝန်ပြောင်းလဲလျှင် User account ကို Admin က ပိတ်ပါ။
- Admin ကို အနည်းဆုံးထားပြီး မိမိ account ကို အခြားသူအား မပေးပါနှင့်။
- Server PC တွင် Windows account password၊ disk encryption (BitLocker) နှင့် automatic screen lock ကို ဖွင့်ထားပါ။
- `.secret_key`, `data/`, `backups/` များကို GitHub/public share သို့ မတင်ပါနှင့်။
- Real employee data မထည့်မီ dummy data ဖြင့် login, role permission, report, backup, restore တို့ကို စမ်းသပ်ပါ။
- PDF ထုတ်ယူပြီး မြန်မာစာ စာလုံးပေါင်း/သရနေရာချထားမှု မှန်ကန်ကြောင်း မျက်မြင်စစ်ဆေးပါ။ ReportLab တွင် Myanmar shaping အကန့်အသတ်ရှိနိုင်သည်။


## အကောင့်ဖွင့်ခြင်းနှင့် Admin ခွင့်ပြုချက်

- အများပြည်သူ/ဝန်ထမ်းများသည် `/signup` မှ Username/Email/Password ဖြင့် အကောင့်ဖွင့်နိုင်သည်။ Google Sign-In ကို ဖွင့်ထားပါက Google Account ဖြင့်လည်း စာရင်းသွင်းနိုင်သည်။
- အသစ်ဖွင့်သမျှအကောင့်များကို `approved=0` အဖြစ်သာ သိမ်းဆည်းသည်။ Admin က `/admin/users` တွင် “ခွင့်ပြုမည်” ကိုနှိပ်မှသာ ဝင်ရောက်ကြည့်ရှုနိုင်သည်။
- ခွင့်မပြုရသေးသူသည် ဝန်ထမ်းစာရင်း၊ ရှာဖွေမှု၊ အစီရင်ခံစာ၊ Export နှင့် Admin စာမျက်နှာများကို မရောက်နိုင်ပါ။ Route အဆင့်တွင်လည်း ခွင့်ပြုချက်စစ်ဆေးထားသည်။
- User Role သည် ကြည့်ရှု/အစီရင်ခံစာထုတ်ယူခွင့်သာရှိသည်။ ဝန်ထမ်းထည့်/ပြင်/ဖျက်နှင့် အလုပ်အကိုင်မှတ်တမ်းပြင်ဆင်ခြင်းကို Admin သာလုပ်နိုင်သည်။
- Google OAuth ဖွင့်ရန် Google Cloud Console တွင် OAuth 2.0 Web Client တစ်ခုဖန်တီးပြီး Authorized Redirect URI ကို `https://YOUR-DOMAIN/auth/google/callback` (LAN အတွက် `http://SERVER-IP:5000/auth/google/callback`) ထည့်ပါ။ `GOOGLE_CLIENT_ID` နှင့် `GOOGLE_CLIENT_SECRET` ကို Environment Variables အဖြစ် ထည့်ပါ။ Google OAuth Client Secret ကို Source Code ထဲ မထည့်ပါနှင့်။
- Google OAuth ကို မသတ်မှတ်ထားလျှင် Google ခလုတ်မပေါ်ဘဲ ပုံမှန် Sign Up အလုပ်လုပ်နေမည်။

အရေးကြီး: ရှိပြီးသား DB အကောင့်များကို schema upgrade က `approved=1` အဖြစ် ဆက်လက်အသုံးပြုနိုင်ရန် ထားသည်။ လက်ရှိအကောင့်အားလုံးကို ပြန်လည်စစ်ဆေးလိုပါက Backup ပြုလုပ်ပြီး Admin DB maintenance ဖြင့် `approved=0` သို့ သတ်မှတ်ပါ။


Google Login သတိပြုရန်: Google OAuth သည် လုံခြုံသော HTTPS callback လိုအပ်သည် (localhost exception မှလွဲ၍)။ LAN IP ဖြင့် `http://192.168.x.x:5000/auth/google/callback` သည် Google OAuth တွင် ပုံမှန်အားဖြင့် လက်မခံနိုင်ပါ။ Google Login သုံးလိုပါက ရုံး၏ internal DNS/domain နှင့် trusted HTTPS certificate သတ်မှတ်ပါ။ မသတ်မှတ်နိုင်သေးလျှင် `/signup` ဖြင့် Local Account ဖွင့်ပြီး Admin ခွင့်ပြုချက်စနစ်ကို အသုံးပြုနိုင်ပါသည်။
