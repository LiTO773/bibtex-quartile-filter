import pandas as pd
import numpy as np
import bibtexparser


def upload_service(bib_file, scimago_file):
    # Read the files
    bib_df = read_bib(bib_file)
    scimago_df = read_scimago(scimago_file)

    # Keep only the journals of the articles
    relevant_journals_df = df_with_bib_journals(bib_df, scimago_df)

    # Fetch the categories
    sorted_categories = fetch_categories(relevant_journals_df)

    return {
        "relevant_journals_df": relevant_journals_df,
        "sorted_categories": sorted_categories,
        "bib_df": bib_df,
    }


def read_bib(file):
    parsed = bibtexparser.load(file)
    df = pd.DataFrame(parsed.entries)
    df["journal"] = df["journal"].str.upper()
    df.dropna(subset=["journal"], inplace=True)
    return df


def read_scimago(file):
    df = pd.read_csv(file, sep=";", encoding="latin-1")
    df = df[["Title", "Categories"]]  # Select only the columns we need
    df["Title"] = df["Title"].str.upper()
    return df


def df_with_bib_journals(bib_df, scimago_df):
    return scimago_df[scimago_df["Title"].isin(bib_df["journal"])]


# Returns an array of [<value> <count>]
def fetch_categories(df):
    categories_arr = np.array([])
    for _, row in df.iterrows():
        categories = row["Categories"].split("; ")
        for category in categories:
            category_without_quartile = category.split(" (Q")[0]
            categories_arr = np.append(categories_arr, category_without_quartile)

    categories_df = pd.DataFrame(categories_arr, columns=["Category"])
    category_counts = categories_df["Category"].value_counts(normalize=False)
    return category_counts


def category_picking_service(previous_results, selected_quartiles, selected_categories):
    quartiles = get_quartiles(selected_quartiles)
    relevant_journals_df = previous_results["relevant_journals_df"]
    bib_df = previous_results["bib_df"]

    # This is not the best (or most efficient) way to do it ¯\_(ツ)_/¯
    combinations = []
    for category in selected_categories:
        for quartile in quartiles:
            combinations.append(f"{category} ({quartile})")

    print(combinations)

    def has_category(x):
        journal_categories = x["Categories"].split("; ")
        print(journal_categories)
        return any(combination in journal_categories for combination in combinations)

    winning_journals = relevant_journals_df[
        relevant_journals_df.apply(has_category, axis=1)
    ]

    winning_articles = bib_df[bib_df["journal"].isin(winning_journals["Title"])]
    return (winning_journals, winning_articles)


def get_quartiles(quartiles_selected):
    print(quartiles_selected)
    quartiles = []
    for i, selected in enumerate(quartiles_selected):
        if selected:
            quartiles.append(f"Q{i+1}")

    return quartiles


def create_bib_file_service(winning_articles):
    df = winning_articles.replace(np.nan, "", regex=True)
    bib = bibtexparser.bibdatabase.BibDatabase()
    bib.entries = df.to_dict("records")
    return bibtexparser.dumps(bib)
