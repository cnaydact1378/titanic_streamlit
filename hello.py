import base64
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR / "타이타닉"
DATA_PATH = PROJECT_DIR / "titanic.csv"
REPORT_PATH = PROJECT_DIR / "final_report_standalone.html"


st.set_page_config(
    page_title="타이타닉 생존 패턴 분석",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


@st.cache_data
def load_report() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def show_report() -> None:
    st.title("타이타닉 생존 패턴 분석")
    st.caption("성별과 객실 등급에 따른 생존 패턴을 정리한 최종 분석 보고서")

    try:
        report_html = load_report()
    except FileNotFoundError:
        st.error(f"보고서 파일을 찾을 수 없습니다: {REPORT_PATH}")
        return

    st.download_button(
        "HTML 보고서 다운로드",
        data=report_html.encode("utf-8"),
        file_name="titanic_survival_report.html",
        mime="text/html",
    )
    encoded_report = base64.b64encode(report_html.encode("utf-8")).decode("ascii")
    st.iframe(
        f"data:text/html;base64,{encoded_report}",
        width="stretch",
        height=1100,
        tab_index=0,
    )


def show_data_explorer() -> None:
    st.title("데이터 탐색")
    st.caption("필터를 조정해 승객 특성과 생존 결과를 직접 살펴보세요.")

    try:
        data = load_data()
    except FileNotFoundError:
        st.error(f"데이터 파일을 찾을 수 없습니다: {DATA_PATH}")
        return

    with st.sidebar:
        st.divider()
        st.subheader("데이터 필터")
        classes = st.multiselect(
            "객실 등급",
            options=sorted(data["Pclass"].dropna().unique()),
            default=sorted(data["Pclass"].dropna().unique()),
            format_func=lambda value: f"{value}등급",
        )
        sexes = st.multiselect(
            "성별",
            options=["female", "male"],
            default=["female", "male"],
            format_func=lambda value: "여성" if value == "female" else "남성",
        )
        survival = st.multiselect(
            "생존 여부",
            options=[1, 0],
            default=[1, 0],
            format_func=lambda value: "생존" if value == 1 else "사망",
        )

    filtered = data[
        data["Pclass"].isin(classes)
        & data["Sex"].isin(sexes)
        & data["Survived"].isin(survival)
    ].copy()

    total = len(filtered)
    survivors = int(filtered["Survived"].sum())
    survival_rate = survivors / total * 100 if total else 0.0
    median_age = filtered["Age"].median()
    median_fare = filtered["Fare"].median()

    metric_cols = st.columns(4)
    metric_cols[0].metric("선택된 승객", f"{total:,}명")
    metric_cols[1].metric("생존율", f"{survival_rate:.1f}%")
    metric_cols[2].metric(
        "중앙 연령", "-" if pd.isna(median_age) else f"{median_age:.1f}세"
    )
    metric_cols[3].metric(
        "중앙 운임", "-" if pd.isna(median_fare) else f"${median_fare:,.2f}"
    )

    if filtered.empty:
        st.warning("선택한 조건에 해당하는 승객이 없습니다.")
        return

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("성별 생존율")
        by_sex = (
            filtered.groupby("Sex", observed=True)["Survived"]
            .mean()
            .mul(100)
            .rename(index={"female": "여성", "male": "남성"})
            .rename("생존율(%)")
        )
        st.bar_chart(by_sex, y_label="생존율 (%)")

    with right:
        st.subheader("객실 등급별 생존율")
        by_class = (
            filtered.groupby("Pclass", observed=True)["Survived"]
            .mean()
            .mul(100)
            .rename(index=lambda value: f"{value}등급")
            .rename("생존율(%)")
        )
        st.bar_chart(by_class, y_label="생존율 (%)")

    st.subheader("승객 데이터")
    display_columns = [
        "PassengerId",
        "Name",
        "Sex",
        "Age",
        "Pclass",
        "Survived",
        "Fare",
        "Embarked",
    ]
    display_data = filtered[display_columns].rename(
        columns={
            "PassengerId": "승객 ID",
            "Name": "이름",
            "Sex": "성별",
            "Age": "나이",
            "Pclass": "객실 등급",
            "Survived": "생존 여부",
            "Fare": "운임",
            "Embarked": "승선 항구",
        }
    )
    display_data["성별"] = display_data["성별"].map(
        {"female": "여성", "male": "남성"}
    )
    display_data["생존 여부"] = display_data["생존 여부"].map(
        {1: "생존", 0: "사망"}
    )
    st.dataframe(display_data, width="stretch", hide_index=True)
    st.download_button(
        "필터 결과 CSV 다운로드",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="titanic_filtered.csv",
        mime="text/csv",
    )


with st.sidebar:
    st.title("🚢 Titanic")
    page = st.radio("메뉴", ["분석 보고서", "데이터 탐색"])
    st.caption("Titanic 승객 891명의 생존 데이터를 분석합니다.")

if page == "분석 보고서":
    show_report()
else:
    show_data_explorer()
