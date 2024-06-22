import streamlit as st
import pandas as pd
from serpapi import GoogleSearch

# Function to retrieve SERP results
def fetch_serp_results(keyword, hl, num_results, device, gl, api_key):
    params = {
        "q": keyword,
        "hl": hl,
        "num": num_results,
        "engine": "google",
        "device": device,
        "gl": gl
    }
    search = GoogleSearch({**params, "api_key": api_key})
    try:
        results = search.get_dict()
        return results.get('organic_results', []), results
    except Exception as e:
        return [], {"error": str(e)}

# Function to display results in a DataFrame
def show_results_with_api_response(keyword, results, response):
    data = []
    for result in results:
        title = result.get('title', 'N/A')
        link = result.get('link', '')
        position = result.get('position', 'N/A')
        if title != 'N/A' and link:
            data.append({"Rank": position, "Title": title, "Link": link})

    if not data:
        st.warning(f"No valid results found for the keyword '{keyword}'.")

    df = pd.DataFrame(data)
    st.subheader(f"Results for the keyword '{keyword}':")
    st.dataframe(df.set_index(df.columns[0]))

    # Display the JSON response
    with st.container():
        st.subheader(f"API Response for '{keyword}':")
        st.json(response, expanded=False)

    return df

# Function to calculate similarity percentage for all results
def compute_global_similarity(results_dfs):
    all_links = [set(df["Link"].apply(lambda x: x)) for df in results_dfs]
    common_links = set.intersection(*all_links) if all_links else set()
    similarity_percentage = len(common_links) / len(all_links[0]) * 100 if all_links and all_links[0] else 0
    return similarity_percentage, common_links

# Function to get user inputs
def retrieve_user_inputs():
    st.title("SERP Comparator")
    st.markdown("### Compare the Google SERP for different keywords.")

    if 'keywords' not in st.session_state:
        st.session_state.keywords = ["", ""]

    if 'params' not in st.session_state:
        st.session_state.params = [{} for _ in st.session_state.keywords]

    st.markdown("#### Enter Keywords and Parameters:")

    for i in range(len(st.session_state.keywords)):
        cols = st.columns([3, 2, 2, 2, 1])
        st.session_state.keywords[i] = cols[0].text_input(f"Keyword {i + 1}", value=st.session_state.keywords[i], key=f'keyword_{i}', placeholder=f"Keyword {i + 1}")
        st.session_state.params[i]["hl"] = cols[1].selectbox("Language (hl)", options=["fr", "en"], index=["fr", "en"].index(st.session_state.params[i].get("hl", "fr")), key=f'hl_{i}')
        st.session_state.params[i]["device"] = cols[2].selectbox("Device", options=["desktop", "mobile"], index=["desktop", "mobile"].index(st.session_state.params[i].get("device", "desktop")), key=f'device_{i}')
        st.session_state.params[i]["gl"] = cols[3].selectbox("Country Code (gl)", options=["fr", "us"], index=["fr", "us"].index(st.session_state.params[i].get("gl", "fr")), key=f'gl_{i}')

        if len(st.session_state.keywords) > 2 and i >= 2:
            remove_button_placeholder = cols[4].empty()
            if remove_button_placeholder.button("❌", key=f'remove_{i}', help="Remove this keyword"):
                del st.session_state.keywords[i]
                del st.session_state.params[i]
                st.experimental_rerun()

    if st.button("Add another keyword"):
        if len(st.session_state.keywords) < 5:
            st.session_state.keywords.append("")
            st.session_state.params.append({})
            st.experimental_rerun()
        else:
            st.warning("You have reached the maximum number of keywords (5).")

    num_results = st.number_input("Enter the number of results to display:", min_value=1, max_value=100, value=10, key='num_results')

    return st.session_state.keywords, num_results, st.session_state.params

# Adding custom CSS for alignment
st.markdown(
    """
    <style>
    .stButton button {
        margin-top: 28px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main function
def main():
    st.sidebar.title("Configuration")
    api_key = st.sidebar.text_input("Enter your SERPAPI API key:", type='password')

    keywords, num_results, params = retrieve_user_inputs()

    if st.button("Compare"):
        api_call_data = []  # Reset API call data on new compare
        results_dfs = []  # Reset results data on new compare
        if not any(keywords):
            st.warning("Please enter at least one keyword to compare.")
        elif not api_key:
            st.warning("Please enter your SERPAPI API key.")
        else:
            retrieving_results_placeholder = st.empty()
            retrieving_results_placeholder.write("Retrieving results...")

            progress_bar = st.progress(0)

            for i, keyword in enumerate(keywords):
                if keyword:
                    param = params[i]
                    # Retrieving and displaying results for each keyword
                    serp_results, full_response = fetch_serp_results(
                        keyword, 
                        param['hl'], 
                        num_results, 
                        param['device'], 
                        param['gl'], 
                        api_key
                    )
                    results_df = show_results_with_api_response(f"{keyword}, {param['hl']}, on {param['device']}, {param['gl']}", serp_results, full_response)
                    results_dfs.append(results_df)
                    api_call_data.append({"keyword": keyword, "response": full_response})

                    # Update the progress bar
                    progress_bar.progress((i + 1) / len(keywords))

            # Remove the "Retrieving results..." message and the progress bar once done
            retrieving_results_placeholder.empty()
            progress_bar.empty()

            # Calculate global similarity
            similarity_percentage, common_links = compute_global_similarity(results_dfs)
            st.write(f"\n**{similarity_percentage:.2f}% of similarity between:**")
            for i, keyword in enumerate(keywords):
                param = params[i]
                st.write(f"- {keyword}, {param['hl']}, on {param['device']}, {param['gl']}")

            # Display similar results in a DataFrame
            if similarity_percentage > 0:
                st.write("\n**Here are the similar results:**")
    
                # Initialize an empty DataFrame with a "Link" column
                common_links_df = pd.DataFrame({"Link": list(common_links)})

                # Add columns for each keyword with their corresponding ranks
                rank_columns = []
                for i, (df, keyword) in enumerate(zip(results_dfs, keywords)):
                    col_name_rank = f"Rank for {keyword}, {params[i]['device']}, {params[i]['hl']}"
                    common_links_df[col_name_rank] = common_links_df["Link"].apply(lambda link: df[df["Link"] == link]["Rank"].values[0] if link in df["Link"].values else None)
                    rank_columns.append(col_name_rank)
    
                # Add titles for the links
                common_links_df["Title"] = common_links_df["Link"].apply(lambda link: df[df["Link"] == link]["Title"].values[0] if link in df["Link"].values else "N/A")
    
                # Reorder columns
                ordered_columns = rank_columns + ["Link", "Title"]
                common_links_df = common_links_df[ordered_columns]
    
                # Display DataFrame with Link column as index
                st.dataframe(common_links_df.set_index(df.columns[2]))

if __name__ == "__main__":
    main()
