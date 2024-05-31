## Py files explanation

As a reminder, when cvv is mentioned, vcc is meant by it.

- cvv_extraction.ipynb is a notebook where (most of) the functions that are used to extract the vccs are shown. It was there to test the components of the szz algo used, but not to take all the vccs of the whole dataset.
- cvv_tools.py is a file where component funcitons (getting commit files and blaming) is located. These functions are used for the overall vcc extraction.
- final_cvv_extraction.py is where the actual extraction of the vcc happens. More on it on section "Extracting the vcc"
- repo_cloning_deck.py is just there because steamdeck was used to extract php metrics (see sibling folder php_metrics), so cloning the php projects there are necessary
- tabulating_vccs.py is a file where the result of the vcc extraction (vcc_results_all_v1.json) is tabulated, which becomes tabulated_commits_v1.json
- extra_scripts.py is there to fix the presentation of error commits (/commit was forgotten).

## Extracting the vcc
This is not done all at once, to ensure that everything works, it is done in several steps, trying first some apps a few times, and then everything (saving the files in between to save progress). 

The errors, (exception caught when trying to get a vcc from a specific commit) are listed in vcc_error_commits_X.json. error commits 2 correspond to vcc resutls test 2, 3 to 3, etc. There's not error commit 1 because I ddint think of it then lol. 

The final result of the vcc extraction is in vcc_results_all_v1.json and the error commits are listed in vcc_error_commits_all_v2. Rerun some of the code to assess where the error comes from (bonus).