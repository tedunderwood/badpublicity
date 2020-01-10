# badpublicity
Code, data, and blog post supporting a presentation at MLA 2020 in Seattle, "No Such Thing as Bad Publicity: Toward a Distant Reading of Reception."

The "toward" in the title signals that this is a teaser presentation on work in progress rather than an argument about results of a completed experiment. So this repo does not contain a fully reproducible workflow--just some code and summary data that may help document "which books I'm talking about." Specifically, we're talking about 58,300 reviews of 8,034 books described in *Book Review Digest* between 1916 and 1930.

The core script here is ```publisher_analysis.py```. This works on raw data (not provided here) to produce ```allbooks.tsv```, ```publishers.tsv```, and ```publisher_books.tsv```. The talk is chiefly based on the last of these three files.

The file ```bestsellers.tsv``` contains the titles of some bestsellers described in *Publishers Weekly* for these years. This is not a complete listing; I've just tried to get 2 or 3 titles for each year, taking them as far as possible from the top five or six titles.

The file ```pulitzer.tsv``` describes winners of the Pulitzer prize for fiction that are mentioned in my data. Note that we lose about 20% of the titles in processing, for instance by being cautious in our author-and-title matching. Note also that for the purposes of the talk I used any book *written by* a Pulitzer-winning author; I'm only working with about a decade of data at the moment, and this strategy gave me a larger data set to talk about. I'll repeat the test with the Pulitzer-winning books themselves when I have enough to be meaningful.

A blog post describing the motives of this work, and some initial exploratory data analysis, is located in the ```/docs``` folder. In my opinion things start getting more fun when you do factor analysis on a matrix where rows are books and columns are different publications, and the cells are filled, for instance, with the number of words publication Y spent on book X. But I didn't have time to discuss that in the talk. For a glimpse of what it might look like, see ```factoranalysis1918.pdf```, but note that some things about 1918 don't generalize to the whole period 1916-30. E.g., the strong negative correlation of sentiment and wordcount does not seem to persist.


