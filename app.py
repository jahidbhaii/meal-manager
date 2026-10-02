
import streamlit as st
from supabase import create_client
from datetime import date
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="Meal Manager", page_icon="🍚", layout="wide")

# ---------- Cloud connection ----------
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")
except Exception:
    st.error("Supabase settings are missing. Add them in Streamlit Cloud → Settings → Secrets.")
    st.stop()

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Simple app gate ----------
if APP_PASSWORD:
    if "meal_logged_in" not in st.session_state:
        st.session_state.meal_logged_in = False
    if not st.session_state.meal_logged_in:
        st.markdown("""
        <style>
        .block-container{max-width:500px;padding-top:10vh}
        </style>
        """, unsafe_allow_html=True)
        st.title("🍚 Meal Manager")
        st.caption("Private group meal system")
        pw=st.text_input("Group Password", type="password")
        if st.button("🔐 Enter", use_container_width=True):
            if pw == APP_PASSWORD:
                st.session_state.meal_logged_in=True
                st.rerun()
            else:
                st.error("Wrong password.")
        st.stop()

# ---------- Styling ----------
st.markdown("""
<style>
.block-container{max-width:1250px;padding-top:1.2rem}
.hero{background:#102a56;color:white;padding:22px 26px;border-radius:16px;margin-bottom:18px}
.hero h1{margin:0}.hero p{margin:5px 0 0;opacity:.85}
.stButton button{border-radius:10px;font-weight:650}
</style>
""", unsafe_allow_html=True)

# ---------- DB helpers ----------
def members():
    r=sb.table("members").select("name").eq("active",True).order("id").execute()
    return [x["name"] for x in r.data]

def get_meal(d,name):
    r=sb.table("meals").select("meals").eq("meal_date",str(d)).eq("member",name).execute()
    return float(r.data[0]["meals"]) if r.data else 0.0

def set_meal(d,name,value):
    sb.table("meals").upsert(
        {"meal_date":str(d),"member":name,"meals":max(0,float(value))},
        on_conflict="meal_date,member"
    ).execute()

def get_bazar(d):
    r=sb.table("bazar").select("amount").eq("bazar_date",str(d)).execute()
    return float(r.data[0]["amount"]) if r.data else 0.0

def set_bazar(d,value):
    sb.table("bazar").upsert(
        {"bazar_date":str(d),"amount":float(value)},
        on_conflict="bazar_date"
    ).execute()

def get_deposit(name):
    r=sb.table("deposits").select("amount").eq("member",name).execute()
    return float(r.data[0]["amount"]) if r.data else 0.0

def set_deposit(name,value):
    sb.table("deposits").upsert(
        {"member":name,"amount":float(value)},
        on_conflict="member"
    ).execute()

def daily_table():
    names=members()
    mr=sb.table("meals").select("meal_date,member,meals").order("meal_date").execute()
    br=sb.table("bazar").select("bazar_date,amount").order("bazar_date").execute()
    m=pd.DataFrame(mr.data or [])
    b=pd.DataFrame(br.data or [])
    if m.empty and b.empty:
        return pd.DataFrame(columns=["Date"]+names+["Total Meal","Total Bazar"])
    dates=set()
    if not m.empty: dates.update(m["meal_date"].tolist())
    if not b.empty: dates.update(b["bazar_date"].tolist())
    rows=[]
    for d in sorted(dates):
        row={"Date":d}
        total=0
        for n in names:
            q=m[(m["meal_date"]==d)&(m["member"]==n)] if not m.empty else pd.DataFrame()
            v=float(q.iloc[0]["meals"]) if not q.empty else 0
            row[n]=v
            total+=v
        q=b[b["bazar_date"]==d] if not b.empty else pd.DataFrame()
        row["Total Meal"]=total
        row["Total Bazar"]=float(q.iloc[0]["amount"]) if not q.empty else 0
        rows.append(row)
    return pd.DataFrame(rows)

def summary():
    names=members()
    df=daily_table()
    total_meal=float(df["Total Meal"].sum()) if not df.empty else 0
    total_bazar=float(df["Total Bazar"].sum()) if not df.empty else 0
    rate=total_bazar/total_meal if total_meal else 0
    rows=[]
    for n in names:
        meal=float(df[n].sum()) if not df.empty else 0
        cost=meal*rate
        dep=get_deposit(n)
        bal=dep-cost
        status="Will Get" if bal>0.005 else ("Will Pay" if bal<-0.005 else "Settled")
        rows.append([n,meal,cost,dep,bal,status])
    return pd.DataFrame(rows,columns=["Member","Total Meal","Meal Cost","Deposit","Balance","Status"]),total_meal,total_bazar,rate

st.markdown('<div class="hero"><h1>🍚 Meal Manager</h1><p>Live cloud meal হিসাব • Everyone sees the same updated data</p></div>',unsafe_allow_html=True)

t1,t2,t3,t4=st.tabs(["🍚 Meal","🛒 Bazar","💰 Deposit","📋 Preview"])

with t1:
    st.subheader("Daily Meal")
    d=st.date_input("Date",date.today(),key="meal_date")
    ns=members()
    if not ns:
        st.warning("No active members.")
    else:
        cols=st.columns(len(ns))
        for i,n in enumerate(ns):
            with cols[i]:
                st.markdown(f"### {n}")
                cur=get_meal(d,n)
                st.metric("Meal",f"{cur:g}")
                if st.button("➕ Add 1",key=f"add_{n}",use_container_width=True):
                    set_meal(d,n,cur+1); st.rerun()
                if st.button("➖ Remove 1",key=f"rm_{n}",use_container_width=True):
                    set_meal(d,n,cur-1); st.rerun()
        with st.expander("Quick Edit / Half Meal"):
            for n in ns:
                c1,c2=st.columns([3,1])
                v=c1.number_input(n,min_value=0.0,value=get_meal(d,n),step=0.5,key=f"qe_{n}")
                if c2.button("Save",key=f"qsave_{n}"):
                    set_meal(d,n,v); st.success(f"{n} saved."); st.rerun()

with t2:
    st.subheader("🛒 Total Bazar")
    d=st.date_input("Bazar Date",date.today(),key="bazar_date")
    amount=st.number_input("Total Bazar (৳)",min_value=0.0,value=get_bazar(d),step=50.0)
    if st.button("💾 Save Total Bazar",use_container_width=True):
        set_bazar(d,amount); st.success("Bazar saved."); st.rerun()
    br=sb.table("bazar").select("bazar_date,amount").order("bazar_date",desc=True).limit(30).execute()
    st.dataframe(pd.DataFrame(br.data or []).rename(columns={"bazar_date":"Date","amount":"Total Bazar"}),
                 use_container_width=True,hide_index=True)

with t3:
    st.subheader("💰 Everyone's Deposit")
    ns=members()
    vals={}
    cols=st.columns(max(1,len(ns)))
    for i,n in enumerate(ns):
        with cols[i]:
            vals[n]=st.number_input(n,min_value=0.0,value=get_deposit(n),step=100.0,key=f"dep_{n}")
    if st.button("💾 Save All Deposits",use_container_width=True):
        for n,v in vals.items(): set_deposit(n,v)
        st.success("All deposits saved."); st.rerun()
    s,tm,tb,rate=summary()
    st.dataframe(s,use_container_width=True,hide_index=True)

with t4:
    st.subheader("📋 Full Excel-style Preview")
    s,total_meal,total_bazar,rate=summary()
    df=daily_table()
    c1,c2,c3=st.columns(3)
    c1.metric("Total Bazar",f"৳{total_bazar:,.2f}")
    c2.metric("Total Meal",f"{total_meal:g}")
    c3.metric("Meal Rate",f"৳{rate:,.2f}")
    st.markdown("### Daily Sheet")
    if df.empty:
        st.info("No data yet.")
    else:
        show=df.copy()
        for col in show.columns:
            if col!="Date":
                show[col]=show[col].map(lambda x:f"{x:g}" if isinstance(x,(int,float)) else x)
        st.dataframe(show,use_container_width=True,hide_index=True,height=380)
    st.markdown("### Final Calculation")
    final=s.copy()
    final["Total Meal"]=final["Total Meal"].map(lambda x:f"{x:g}")
    for col in ["Meal Cost","Deposit","Balance"]:
        final[col]=final[col].map(lambda x:f"৳{x:,.2f}")
    st.dataframe(final,use_container_width=True,hide_index=True)
    out=BytesIO()
    with pd.ExcelWriter(out,engine="openpyxl") as w:
        df.to_excel(w,index=False,sheet_name="Meal Sheet")
        s.to_excel(w,index=False,sheet_name="Final Summary")
    st.download_button("📥 Download Full Excel",out.getvalue(),"Meal_Full_Report.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)

st.caption("☁️ Live cloud database • Changes are shared across users")
