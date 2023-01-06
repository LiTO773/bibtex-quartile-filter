import streamlit as st
from streamlit import caching
from services import upload_service, category_picking_service, create_bib_file_service

# Stages
UPLOAD_STAGE = 1
CATEGORY_PICKING_STAGE = 2
RESULTS_STAGE = 3

if "stage" not in st.session_state:
    st.session_state.stage = UPLOAD_STAGE

if "upload_results" not in st.session_state:
    st.session_state.upload_results = {
        "relevant_journals_df": None,
        "sorted_categories": None,
        "bib_dict": None,
    }

if "selected_quartiles" not in st.session_state:
    st.session_state.selected_quartiles = [False] * 4

if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = []

if "winners" not in st.session_state:
    st.session_state.winners = None


def set_stage(stage):
    st.session_state.stage = stage


def set_selected_quartile(i):
    st.session_state.selected_quartiles[i] = not st.session_state.selected_quartiles[i]


def append_select_categories(category):
    st.session_state.selected_categories = st.session_state.selected_categories + [
        category
    ]


def set_upload_results(upload_results):
    st.session_state.upload_results = upload_results


def set_winners(winners):
    st.session_state.winners = winners


# Views
st.set_page_config(
    page_title="BibTeX Journal Quartile Filter", layout="wide", page_icon="📚"
)


def upload_view():
    st.header("File upload")
    bib_file = st.file_uploader("Upload your BibTeX file", type="bib")
    "Upload your Scimago's CSV Ratings. You can find it here: https://www.scimagojr.com/journalrank.php"
    scimago_file = st.file_uploader("Upload your Scimago's CSV Ratings", type="csv")

    def on_click():
        if bib_file and scimago_file:
            upload = upload_service(bib_file, scimago_file)
            set_upload_results(upload)
            set_stage(CATEGORY_PICKING_STAGE)
        else:
            st.error("Please upload both files")

    st.button("Next", on_click=on_click)


def category_picking_view():
    st.header("Quartiles")
    st.write("Select which quartiles you want to keep")

    def quartile_picker(i):
        def pick():
            set_selected_quartile(i)

        return pick

    col1, col2, col3, col4 = st.columns(4)
    col1.checkbox("Q1", on_change=quartile_picker(0))
    col2.checkbox("Q2", on_change=quartile_picker(1))
    col3.checkbox("Q3", on_change=quartile_picker(2))
    col4.checkbox("Q4", on_change=quartile_picker(3))

    st.header("Available categories")
    st.write("Select the journal categories you want to keep")

    for category, count in st.session_state.upload_results["sorted_categories"].items():

        def on_change_w_category(selected_category):
            def on_change():
                append_select_categories(selected_category)

            return on_change

        st.checkbox(
            f"{category} (appears **{count}** times)",
            on_change=on_change_w_category(category),
        )

    def on_click():
        if not any(st.session_state.selected_quartiles):
            st.error("Please select at least one quartile")
        else:
            results = category_picking_service(
                st.session_state.upload_results,
                st.session_state.selected_quartiles,
                st.session_state.selected_categories,
            )
            set_winners(results)
            set_stage(RESULTS_STAGE)

    st.button("Next", on_click=on_click)


def results_view():
    winning_journals, winning_articles = st.session_state.winners
    st.header("Results")
    st.write(f"Here are the **{len(winning_journals)}** winning journals")
    st.dataframe(winning_journals)
    st.write(f"Here are the **{len(winning_articles)}** winning articles")
    st.dataframe(winning_articles[["doi", "title", "journal"]])

    data = create_bib_file_service(winning_articles)

    st.download_button(
        "Download winning articles as BibTeX",
        data=data,
        file_name="winning_articles.bib",
        mime="application/x-bibtex",
    )

    st.button("Restart", on_click=lambda: caching.clear_cache())


if st.session_state["stage"] == UPLOAD_STAGE:
    upload_view()
elif st.session_state["stage"] == CATEGORY_PICKING_STAGE:
    category_picking_view()
else:
    results_view()
