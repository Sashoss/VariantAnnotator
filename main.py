from VariantAnnotator import *

ParseObj = Parser("test_vcf_data1.txt")
variants = ParseObj.parseInput()
ANNOTATE(variants, output="myOutputFile.xlsx")