## To do
Its done now :)
        

## Files explanations
- php_metrics_extraction_tools.py -> functions needed for extraction
- php_metrics_extraction_exec.py -> overarching execution (+ a bit of testing)
- extra_scripts -> as the name suggests, explanation of what exactly it is for is in the file itself
- clean_concat_data -> Cleaning the data once all metrics are gathered
- extracting_joris_commits -> anything to do with it
- duplicates from v11 -> As the name suggests, it lists the duplicates of tabulated_commits_v11_nov.json
## Tabulated Commits files explanations

nov = no original_vuln attribute

**The Overall Process**

From vcc_results_all_v1 we tabulated it, then it got to tabulated v1. There are some steps to extract the php metrics:
1. Process the changed files: this is done by prepare_files(...) in php_metrics_extraction tool. The name of the changed files are obtained, then from there we copy the changed files (of that commit) to a temp folder.
2. run pdepend: done by run_pdepend(...), this is simply running pdepend in the command line
3. parse_xml(...): This function parses the sum.xml provided by the pdepend tool after running it. It parses and returns a dictionary that summarizes the metrics needed in commit level.
4. clear_temp_files(...): This func clear all the temp files, namely the changed files of the commit and the sum.xml.

This is done for every commit in the tabulated_commits_vX. See the php_metrics_extraction_exec.py to see how it's done exactly. Errors are possible and that's why the main function to extract the metrics (get_commit_metrics(...)) is wrapped in a try catch statement. If it's an error, then the metric commit["php_metrics_extracted"] is -1. The ones that are not attempted on is 0 and the ones that have been succesfully extracted is 1.

The code could be run from tabulated v1, but we took it step by step to test on some apps first (and not others) to see if it all works fine. See the section "versions".

In v9, the data is cleaned, this simply means turning some of the variables to bool, ensuring that every commit has all the features etc. Before going to tabulated v10, joris filtered commits need to be discussed.

Joris filtered commits are extra commits that comes from Joris because we want more random neutral commits. See joris_commits(_filtered) section for more details on this. The result (joris v5) is then concatted with tabulated v9 which gives v10.

Joris also had these same commits (mostly, there are some non-overlaps for some reason lol) with extra git metrics, this is git_metrics_commits.json, which is just the metrics from joris_jsons/ProcessFeatures_allCommits concatted. It is then all combined in v11.

To give overall numbers, 4096 commits at the end are obtained in v13 (including error, excluding duplicates, including neutral commits). Whereas we started with about 3000 commits in v1 (non neutral, with half of it being duplicates). Out of the 4000ish commits about 900 are vulnerable and about 2300 are neutral (These numbers are estimate, to know the exact number just write some scripts).

**Some Extra Notes**

- There are duplicates in tabulated v1 until v5. This is removed in v6, however in v6, it was not taken into account that **some of the duplicate shas had different labels**, these are removed only in v13. This can be explained by the fact that most of this come from pull commits, which come after each other.
- In v11, there are also duplicates, which is (carelessly) removed in v12. However, some of these ones also have different labels and neutrality, this is our own error and not from the actual source. These were taken care of in v13.
- The overall process's duration really depends on the machine. In a laptop aspire 3 (Yeska's laptop) the extraction takes very long as starting the tool pdepend takes a while, and the computing is also very slow. When SteamDeck is used to run this code, it runs very fast. With the laptop, 800 commits were extracted for tabulated v4 and it took 11 hours (to be fair, there were duplicates of commits containing thousands of changed files, making the pdepend tool running way more). With the steam deck, getting joris_filtered_v4 (so about 2000ish) commits took about 3 hours.

### Versions
1. v1 = the first one out of vcc_extraction (named cvv_extraction because I'm dumb)
2. Adds extra attributes: php_metrics_extracted and appname
3. First test of consolidation, tested on one app: Friendica. 
4. Kanboard and OwnCloud added
5. NextCloud, Microweber, Pimcore added
6. Duplicates are removed
7. Nextcloud is redone (to test differentiating error and no php file), plus tuleap, piwigo, and shopware
8. Every other application is added is added
9. Cleaned (see clean_concat_data.py)
10. Concatted with joris_filtered_v5
11. Merged with the git metrics commits
12. Removed some duplicates, but some of the (former) duplicates labels and neutrality is wrong
13. Fixed the wrong former duplicates neutrality and label, also removed ambigous labels: Some sha are both fixing commit and vcc, these are removed.

## joris_commits(_filtered)
Joris mined extra random commits for non-vulnerable commits. It's from joris_jsons/random-commits... In the folder there are multiple jsons, one for each app. It had to be concat. joris_commits.json is the result of the first concat, resulting in 4410 commits in total (this includes commits that are already from Yeska). 

This needs to be filtered, so that php metrics extraction is only done in non-Yeska commits, in other words commits that are not in tabulated_commits_v6^. The result is the filtered version
### (Filtered) Versions
1. First filtration using extractin_joris_commits.remove_overlaps()
2. Actually same as the first one, just used different method to filter which is extractin_joris_commits.remove_overlaps_v2()
3. Added php_metrics_extracted to track errors
4. Everything extracted.
5. Cleaned

## Extra notes
- Apparently there are duplicates in the joris_commits, but it's removed with remove_overlaps().
- There's only 38 projects here! Two turned out didnt have any references_transformed (see cvv extraction)
- Hestia and Vesta are the same applications???