


class Parser:
    def __init__(self, filename):
        self.filename = filename

    def parseInput(self):
        fdata = open(self.filename)
        store_variants = list()
        for line in fdata:
            if line.count("#") == 1:
                store_headers = line.lstrip("#").strip().split("\t")
            elif "#" not in line:
                store_vars = dict()
                lobj = line.strip().split("\t")
                for i, j in zip(store_headers, lobj):
                    store_vars[i] = j

                store_vars["parsed_INFO"] = self._parseInfo(store_vars["INFO"])
                store_vars["parsed_SAMPLE"] = self._parseSample(store_vars["FORMAT"], store_vars["sample"])

                store_variants.append(store_vars)

        return store_variants

    def _parseInfo(self, infoVar):
        storeInfo = dict()
        infoData = infoVar.strip().split(";")
        for dataObj in infoData:
            varObj = dataObj.split("=")
            var = varObj[0]
            val = varObj[1]
            storeInfo[var] = val

        return storeInfo

    def _parseSample(self, formatVar, sampleVar):
        storeSample = dict()
        sampleData = sampleVar.strip().split(":")
        formatData = formatVar.strip().split(":")
        for i, j in zip(formatData, sampleData):
            storeSample[i] = j

        return storeSample



