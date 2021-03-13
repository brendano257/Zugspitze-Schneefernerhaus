#!/usr/bin/env bash

# This probably won't work for you!
# It's a Linux bash script that uses ImageMagick to convert all pngs in a specific folder to a single pdf.
# It could be tweaked for Windows or another system/converter, but I've done it here for convenience.

convert flagged_data_comparisons/*.png "./flagged_data_comparisons.pdf"
