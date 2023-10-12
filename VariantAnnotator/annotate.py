

import asyncio
import aiohttp
import requests, sys
from tqdm import tqdm
import xlsxwriter

class ANNOTATE:
    """
        Adds annotations for each variants in vcf file using Ensembl database.
        Curently it uses grch37 human genome to annotate variants
        Make sure your alignment was conducted using grch37 human reference genome
    """

    def __init__(self, variantsList, output="output.xlsx"):
        self.server = "https://grch37.rest.ensembl.org"
        self.ext = "/vep/human/hgvs"
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.variantsList = variantsList
        self.outfile = output
        asyncio.run(self.process_variants())


    def get_consequence(self, store_data, mutResults):
        """
        :param store_data: Input dictionary to store the annotations
        :param mutResults: json annotations for a specific variant returned from ensembl server
        :return: populated store_data dictionary
        """
        try:
            store_data[mutResults['input']]['gene_name'] = mutResults['transcript_consequences'][0]['gene_symbol']
            store_data[mutResults['input']]['gene_id'] = mutResults['transcript_consequences'][0]['gene_id']
            store_data[mutResults['input']]['transcript_id'] = mutResults['transcript_consequences'][0]["transcript_id"]
            store_data[mutResults['input']]['variant_biotype'] = mutResults['transcript_consequences'][0]["biotype"]
            store_data[mutResults['input']]['regulatory_consequence'] = {"consequence_terms": mutResults['regulatory_feature_consequences'][0]["consequence_terms"][0], "regulatory_feature_id": mutResults['regulatory_feature_consequences'][0]["regulatory_feature_id"]}
        except:
            store_data[mutResults['input']]['gene_name'] = ""
            store_data[mutResults['input']]['gene_id'] = ""
            store_data[mutResults['input']]['transcript_id'] = ""
            store_data[mutResults['input']]['regulatory_consequence'] = {"consequence_terms": "", "regulatory_feature_id": ""}
            store_data[mutResults['input']]['variant_biotype'] = ""

        try:
            store_data[mutResults['input']]['sift_prediction'] = mutResults['transcript_consequences'][0]["sift_prediction"]
            store_data[mutResults['input']]['polyphen_prediction'] = mutResults['transcript_consequences'][0]["polyphen_prediction"]
            store_data[mutResults['input']]['amino_acids'] = mutResults['transcript_consequences']["amino_acids"]
            store_data[mutResults['input']]['codons'] = mutResults['transcript_consequences']["codons"]
        except:
            store_data[mutResults['input']]['sift_prediction'] = ""
            store_data[mutResults['input']]['polyphen_prediction'] = ""
            store_data[mutResults['input']]['amino_acids'] = ""
            store_data[mutResults['input']]['codons'] = ""

        return store_data

    def dbAnnotations(self, store_data, mutResults, annot_section):
        """
        :param store_data: Input dictionary to store the annotations
        :param mutResults: json annotations for a specific variant returned from ensembl server
        :param annot_section: Specific annotation section within multiple annotations within the 'colocated_variants' of variant annotation json data
        :return: populated store_data dictionary
        """
        if annot_section['strand']:  # lazy trick to check if the annotation contains rs id
            store_data[mutResults['input']]['rsId'] = annot_section['id']
        else:
            store_data[mutResults['input']]['rsId'] = ""


        try:
            if annot_section["allele_string"] == "COSMIC_MUTATION":
                store_data[mutResults['input']]['cosmic_Ids'] = annot_section['id']
        except:
            store_data[mutResults['input']]['cosmic_Ids'] = ""

        try:
            store_data[mutResults['input']]['pubmed_Ids'] = ";".join(annot_section['pubmed'])
        except:
            store_data[mutResults['input']]['pubmed_Ids'] = ""

        try:
            store_data[mutResults['input']]['Uniprot_Ids'] = ";".join(annot_section['var_synonyms']['UniProt'])
        except:
            store_data[mutResults['input']]['Uniprot_Ids'] = ""

        try:
            store_data[mutResults['input']]['Clinvar_Ids'] = ";".join(annot_section['var_synonyms']['Clinvar'])
        except:
            store_data[mutResults['input']]['Clinvar_Ids'] = ""

        try:
            store_data[mutResults['input']]['PharmGKB_Ids'] = ";".join(annot_section['var_synonyms']['PharmGKB'])
        except:
            store_data[mutResults['input']]['PharmGKB_Ids'] = ""

        return store_data

    def mutFrequency(self, store_data, mutResults, annot_section):
        """
        pull variant frequency across different populations
        :param store_data: Input dictionary to store the annotations
        :param mutResults: json annotations for a specific variant returned from ensembl server
        :param annot_section: Specific annotation section within multiple annotations within the 'colocated_variants' of variant annotation json data
        :return: populated store_data dictionary
        """
        try:
            store_data[mutResults['input']]['nuc_frequency'] = dict()
            annot = annot_section['frequencies']
            for skey, sval in annot.items():
                store_data[mutResults['input']]['nuc_frequency']['african_freq'] = sval['afr']
                store_data[mutResults['input']]['nuc_frequency']['southAsian_freq'] = sval['sas']
                store_data[mutResults['input']]['nuc_frequency']['eastAsian_freq'] = sval['eas']
                store_data[mutResults['input']]['nuc_frequency']['american_freq'] = sval['amr']
                store_data[mutResults['input']]['nuc_frequency']['european_freq'] = sval['eur']
        except:
            store_data[mutResults['input']]['nuc_frequency'] = {'african_freq': "", 'southAsian_freq': "", 'eastAsian_freq': "", 'american_freq': "", 'european_freq': ""}

        return store_data

    async def get_variant_info1(self, variants, store_data):
        async with aiohttp.ClientSession() as session:

            # Create a string to hold the 200 variants
            variants_list = '{ "hgvs_notations" : ['
            # Loop through each variant and append it to the list
            for variantObj in variants:
                variants_list = variants_list + '"' + variantObj["CHROM"]+':g.'+variantObj["POS"]+variantObj["REF"]+'>'+variantObj["ALT"] + '" ,'

            inpData = variants_list.rstrip(',') + ' ]}'
            try:
                async with session.post(self.server + self.ext, headers=self.headers, data=inpData) as r:
                    if r.status != 200:
                        print(f"Failed with status {r.status}")
                        print(f"Response content: {await r.text()}")
                        return store_data

                    output = await r.json()
                    for mutResults in output:
                        store_data[mutResults['input']] = dict()
                        var_annotation = mutResults['colocated_variants']
                        for annot_section in var_annotation:
                            store_data = self.get_consequence(store_data, mutResults)
                            store_data = self.dbAnnotations(store_data, mutResults, annot_section)
                            store_data = self.mutFrequency(store_data, mutResults, annot_section)

                        try: # dirty hack to make sure cosmic id key is populated if missed earlier.
                            store_data[mutResults['input']]['cosmic_Ids']
                        except:
                            store_data[mutResults['input']]['cosmic_Ids'] = ""

            except Exception as e:
                print(f"An error occurred: {str(e)}")
                sys.exit()

        return store_data

    def write_excel(self, store_data):
        workbook = xlsxwriter.Workbook(self.outfile)
        worksheet = workbook.add_worksheet()

        # Cell border formats
        bold_format = workbook.add_format({'bold': True, 'bottom': 2, 'align': 'center'})
        bold_border_format = workbook.add_format({'bold': True, 'bottom': 6, 'top': 2, 'align': 'center'})
        left_bold_format = workbook.add_format({'bold': True, 'left': 2, 'bottom': 2, 'align': 'center'})
        left_format = workbook.add_format({'left': 2, 'align': 'center'})
        right_bold_format = workbook.add_format({'bold': True, 'right': 2, 'bottom': 2, 'align': 'center'})
        right_format = workbook.add_format({'right': 2, 'align': 'center'})
        bottom_bold_format = workbook.add_format({'bottom': 2, 'align': 'center'})
        center_format = workbook.add_format({'align': 'center'})

        # Merged top-level headings
        worksheet.merge_range('A1:G1', 'Base Information', bold_border_format)
        worksheet.merge_range('H1:L1', 'Database Ids', bold_border_format)
        worksheet.merge_range('M1:N1', 'Mutation Scores', bold_border_format)
        worksheet.merge_range('O1:S1', 'Mutation Frequency', bold_border_format)
        worksheet.merge_range('T1:U1', 'Literature', bold_border_format)

        # Sub-headings
        base_info_sub_headings = ['Mutation', 'Gene name', 'Variant biotype', 'Regulatory significance', 'Regulatory feature id', 'Amino acids', 'Codons']
        database_ids_sub_headings = ['rsid', 'Uniprot id', 'Cosmic id', 'Clinvar id', 'PharmGKB ID']
        mutation_scores_sub_headings = ['SIFT', 'Polyphen']
        mutation_frequency_sub_headings = ['American', 'South Asian', 'East Asian', 'African', 'European']
        literature_sub_headings = ["Pubmed", "PMC"]

        worksheet.write_row('A2', base_info_sub_headings, bold_format)
        worksheet.write('H2', database_ids_sub_headings[0], left_bold_format)
        worksheet.write_row('I2', database_ids_sub_headings[1:], bold_format)
        worksheet.write('M2', mutation_scores_sub_headings[0], left_bold_format)
        worksheet.write('N2', mutation_scores_sub_headings[1], bold_format)
        worksheet.write('O2', mutation_frequency_sub_headings[0], left_bold_format)
        worksheet.write_row('P2', mutation_frequency_sub_headings[1:], bold_format)
        worksheet.write_row('T2', literature_sub_headings, right_bold_format)

        row = 2
        for key, inputVariantData in store_data.items():
            row_data = [
                key,
                inputVariantData['gene_name'],
                inputVariantData['variant_biotype'], inputVariantData['regulatory_consequence']['consequence_terms'],
                inputVariantData['regulatory_consequence']['regulatory_feature_id'], inputVariantData['amino_acids'],
                inputVariantData['codons'],
                inputVariantData['rsId'], inputVariantData['Uniprot_Ids'], inputVariantData['cosmic_Ids'],
                inputVariantData['Clinvar_Ids'], inputVariantData['PharmGKB_Ids'],
                inputVariantData['sift_prediction'], inputVariantData['polyphen_prediction'],
                inputVariantData['nuc_frequency']['american_freq'],
                inputVariantData['nuc_frequency']['southAsian_freq'],
                inputVariantData['nuc_frequency']['eastAsian_freq'], inputVariantData['nuc_frequency']['african_freq'],
                inputVariantData['nuc_frequency']['european_freq'],
                inputVariantData['pubmed_Ids'],
                "", # leaving PMC empty here at the moment
            ]

            for col, data in enumerate(row_data):
                if col in [7, 12, 14, 19, 21]:
                    worksheet.write(row, col, data, left_format)
                elif col == 20:
                    worksheet.write(row, col, data, right_format)
                else:
                    worksheet.write(row, col, data, center_format)

            row += 1

        # Add bottom borders for headers and sub-headers
        worksheet.conditional_format(f'A1:U{row}',{'type': 'formula', 'criteria': 'ROW()=1', 'format': bottom_bold_format})
        worksheet.conditional_format(f'A2:U{row}',{'type': 'formula', 'criteria': 'ROW()=2', 'format': bottom_bold_format})

        workbook.close()


    async def process_variants(self):
        # Splitting variants into batches of 10
        batches = [self.variantsList[i:i + 10] for i in range(0, len(self.variantsList), 10)]
        store_data = dict()
        # Processing each batch asynchronously
        pbar = tqdm(total=len(batches))
        for batch in batches:
            store_data = await self.get_variant_info1(batch, store_data)
            pbar.update(1)

        self.write_excel(store_data)


