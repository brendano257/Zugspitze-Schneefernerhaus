#!/usr/bin/env bash

convert plots/filtered_JFJ/full/*.png "plots/pdfs/filtered_JFJ_full_plot.pdf"
convert plots/filtered_JFJ/new/*.png "plots/pdfs/filtered_JFJ_new_only_plot.pdf"

convert plots/unfiltered_JFJ/full/*.png "plots/pdfs/unfiltered_JFJ_full_plot.pdf"
convert plots/unfiltered_JFJ/new/*.png "plots/pdfs/unfiltered_JFJ_new_only_plot.pdf"
