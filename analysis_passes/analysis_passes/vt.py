import requests
import sys

class VT:

    keys = ['e43751c0e33926da35e1832aec4b4dbcad650844cdfdad74336afc17070273b7', 
            '4be42a9328e351a5d44c4d7de9e46a3076c83236b09dbb8ba1d3f3a4f793d428',
            'ecd9836bbaaa59a929848339ad7de69180765351e1160d99e1b90cb5d9bfdc4c',
            '0b6a711b11ab64cb583753bebdd1983beea944c0a3c877c75b754770f58072d4',
            'fb21dffe1a2a1c8e56029b3bd8709f4b0d96e2b0d70f1fcfb4a90ded80284160',
            '1ef76d73e4dbb0bd24b7501e745516dea9631ef8cfd5b66d5d69d06fc2460bfb',
            '665d0a6a9ef8f264ac2f490780b9d703d600fe8fc2a20fb2590d63ab4856cee4',
            '0d736703427883406197dec218c4b1ae388498a3c331c957375eb93e3172059c', 
            '734d9544bd269c15edb8029c5b61b5d39ebe332f52a07659352d2223dafbaa8f',
            '8b81b9a4525ad2310bae4dab0ceea573cbc53efee72640a039606d95c1183869',
            'e6e67a2324db98b444a17d947d3a434f8dff911f627f43db7308399ed0ba549f',
            'a43d8e38b1ef9272ce67bca3c81027ea42c45dd0a9d57b62f4056e5d6cc3ebd9',
            '0e13f1c57fbd8a6ce0a3dfcb18f589a169ec882a6c864922812b13286d3718b3',
            'ade2abeacb8053136ea3ddfc035e462955d7808910c7747f0903afeff000251c',
            'f2769be661d0e3e02a1a4279fa11c38b788f0bd7d9b0e4f24134c9e6349c0c8b',
            'f4516f055aed70057661b9b8a1e58ae3a60e1e7add321e1f1ae36224568138cc',
            '5ae0c536b939534b2cc0725ae4db6f57aff4cdea3015a3d6bacfc3f369815f9a',
            '906841870e5f6a8c0fb8506ba17580b406de0de74024ebbc1da415a028d3b973',
            'a9248dcd05624e5505a26ae6f0e52f505617e8b72dd8059532f7a6dbce16ed62',
            'fc701b7a9913978bb4575fa3003e0122a112537a90795819f742a81b6cc027dd',
            '874faeca9a5a8f76389a876f760adb6a10aa4ce8d30e36632d5cc79d0d0e81d6',
            'f83104656be33b32afe29d9b066e76f54a745d2d678c8e92b34bdd186e772216',
            '272d3bf38d1c5b04703b05de324ab368b59eed20d7d5ee786b2bc657063ee9c8']

    #academic_key = 'e43751c0e33926da35e1832aec4b4dbcad650844cdfdad74336afc17070273b7' # Omar's Academic API key
    academic_key = '0b6a711b11ab64cb583753bebdd1983beea944c0a3c877c75b754770f58072d4' # Eric's Academic API key
    key_flag = 0
    upload_count = 0

    def __init__(self):
        self.upload_files = []
        self.ufpath = ''
        self.api_key = ''
        self.api_url = 'https://www.virustotal.com/vtapi/v2/'
        self.proxies = None
        self.num_204 = 0

    def scan_url(self, this_url, timeout=None):
        params = {'apikey': self.api_key, 'url': this_url}
        try:
            response = requests.post(self.api_url + 'url/scan', params=params, proxies=self.proxies, timeout=timeout)
        except requests.RequestException as e:
            return dict(error=str(e))

        scan =  _return_response_and_status_code(response)
        if ('error' not in scan): #and ('results' in scan):
            if scan['results']['response_code'] == 1:
                return "PASS"               
            else:
                #return "FAIL"
                return scan
        elif scan['response_code'] == 204:
            self.num_204 += 1
            if (self.num_204 == len(self.keys)):
                #return "FAIL"
                return scan
            self.key_flag = (self.key_flag + 1) % len(self.keys)
            self.setkey(self.keys[self.key_flag])
            return self.scan_url(this_url)
        else:
            return scan
            #return "FAIL"

    def get_url_report(self, this_url, scan='0', timeout=None):
        """ Get the scan results for a URL. (can do batch searches like get_file_report)
        :param this_url: a URL will retrieve the most recent report on the given URL. You may also specify a scan_id
                         (sha256-timestamp as returned by the URL submission API) to access a specific report. At the
                         same time, you can specify a CSV list made up of a combination of hashes and scan_ids so as
                         to perform a batch request with one single call (up to 4 resources per call with the standard
                         request rate). When sending multiples, the scan_ids or URLs must be separated by a new line
                         character.
        :param scan: (optional): this is an optional parameter that when set to "1" will automatically submit the URL
                      for analysis if no report is found for it in VirusTotal's database. In this case the result will
                      contain a scan_id field that can be used to query the analysis report later on.
        :param timeout: The amount of time in seconds the request should wait before timing out.
        :return: JSON response
        """
        params = {'apikey': self.api_key, 'resource': this_url, 'scan': scan}

        try:
            response = requests.get(self.api_url + 'url/report', params=params, proxies=self.proxies, timeout=timeout)
        except requests.RequestException as e:
            return dict(error=str(e))

        rep =  _return_response_and_status_code(response)
        if ('error' not in rep): 
            if rep['results']['response_code'] == 1:
                return rep               
            else:
                #return "FAIL"
                return dict(error=rep)
        elif scan['response_code'] == 204:
            self.num_204 += 1
            if (self.num_204 == len(self.keys)):
                #return "FAIL"
                return dict(error="204 on all API keys")
            self.key_flag = (self.key_flag + 1) % len(self.keys)
            self.setkey(self.keys[self.key_flag])
            return self.get_url_report(this_url)
        else:
            return "FAIL"

    # set the file path containing all urls to be examined
    def setufpath(self, ufpath):
        self.ufpath = ufpath

    # set a new api-key
    def setkey(self, key):
        self.api_key = key

    # set an output file path
    def setofile(self, ofile):
        self.ofile = ofile

    # set an output file path only contains malicious results
    def setomfile(self, omfile):
        self.omfile = omfile

def run_VT_scan(link):
    vt = VT()
    vt.setkey(vt.keys[vt.key_flag])
    vt.num_204 = 0

    vt.upload_files.append(link)

    avlist = []
    for url in vt.upload_files:
        #print("Scanning URL")
        vt.num_204 = 0
        scan = vt.scan_url(url)
        #print("Returned SCAN", scan)
        if scan == "PASS":
            vt.num_204 = 0
            getr = vt.get_url_report(url)
            if getr != "FAIL":    
                if ('error' not in getr) and ('results' in getr):
                    if getr['results']['positives'] > 0:
                        for av in getr['results']['scans']:
                            if getr['results']['scans'][av]['detected']:
                                avlist.append('+ ' + av + ':  ' + getr['results']['scans'][av]['result'])
                #print(avlist)
                return avlist
            else:
                return "GET_REPORT_FAIL" 
        else:
            #return "SCAN_FAIL"
            return scan 


def _return_response_and_status_code(response, json_results=True):
    """ Output the requests response content or content as json and status code
    :rtype : dict
    :param response: requests response object
    :param json_results: Should return JSON or raw content
    :return: dict containing the response content and/or the status code with error string.
    """
    if response.status_code == requests.codes.ok:
        return dict(results=response.json() if json_results else response.content, response_code=response.status_code)
    elif response.status_code == 400:
        return dict(
            error='package sent is either malformed or not within the past 24 hours.',
            response_code=response.status_code)
    elif response.status_code == 204:
        return dict(
            error='You exceeded the public API request rate limit (4 requests of any nature per minute)',
            response_code=response.status_code)
    elif response.status_code == 403:
        return dict(
            error='You tried to perform calls to functions for which you require a Private API key.',
            response_code=response.status_code)
    elif response.status_code == 404:
        return dict(error='File not found.', response_code=response.status_code)
    else:
        return dict(response_code=response.status_code)

if __name__ == "__main__":
    run_VT_scan(sys.argv[1])    
