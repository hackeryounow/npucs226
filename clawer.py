import argparse
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import bibtexparser as bp
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
import time

from nltk import deprecated

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 '
                  'Safari/537.36 '

}

scholar_url = "https://scholar.google.com.hk/scholar?start=%d&q=%s&hl=zh-CN&as_sdt=0," \
              "5&as_ylo=%s&as_yhi=%s"
cite_url = "https://scholar.google.com.hk/scholar?q=info:%s:scholar.google.com/&output=cite&scirp=%d&hl=zh-CN"

letpub_search_url = "https://www.letpub.com.cn/index.php?page=journalapp&view=search"
headers_post = {
    "User-Agent": headers['User-Agent'],
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.letpub.com.cn",
    "Origin": "http://www.letpub.com.cn",
    "Referer": "http://www.letpub.com.cn/index.php?page=journalapp&view=search"
}
form_data = {
    "searchname": "IEEE Communications Surveys and Tutorials",
    "searchissn": "",
    "searchfield": "",
    "searchimpactlow": "",
    "searchimpacthigh": "",
    "searchscitype": "",
    "view": "search",
    "searchcategory1": "",
    "searchcategory2": "",
    "searchjcrkind": "",
    "searchopenaccess": "",
    "searchsort": "relevance",
}


def journal_char2word(journal):
    return journal.replace(r"&", "and")


def clawOnePage(_scholar_url, start=0):
    resp_scholar = requests.get(_scholar_url, headers=headers)
    bs_search = BeautifulSoup(resp_scholar.text, 'html.parser')
    raw_items = bs_search.find_all(class_='gs_r gs_or gs_scl')

    idx = start
    papers = []
    for raw_item in raw_items:
        paper = {}
        label_a = raw_item.select('h3 > a')[0]
        paper['paper_id'] = label_a['id']
        paper['paper_url'] = label_a['href']

        paper['paper_name'] = label_a.text
        print("name: %s, link: %s" % (paper['paper_name'], paper['paper_url']))
        paper['keyword_loc_content'] = raw_item.select('.gs_rs')[0].text
        cite_num_str = raw_item.select('.gs_fl > a')[2].text
        paper['cite_num'] = re.search(r"\d+", cite_num_str).group()
        _cite_url = cite_url % (paper['paper_id'], idx)
        resp_cite = requests.get(_cite_url, headers=headers)
        bs_cite = BeautifulSoup(resp_cite.text, 'html.parser')
        bibTeX_url = bs_cite.select('.gs_citi')[0]['href'].replace("\n", "")
        # print(bibTeX_url)
        resp_bibTeX = requests.get(bibTeX_url, headers=headers)
        bib_str = resp_bibTeX.text
        # print(bib_str)
        paser = BibTexParser()
        paser.customization = convert_to_unicode
        bibdata = bp.loads(bib_str, parser=paser)
        entry = bibdata.entries[0]
        # bibTeX解析，期刊名，时间，页码，作者
        paper['journal'] = journal_char2word(entry.get('journal', ""))
        if paper['journal'] == "":
            journal_char2word(entry.get('booktitle', ""))
        paper['year'] = entry['year']
        paper['pages'] = entry['pages'].replace("--", "-")
        paper['volume'] = entry.get('volume', "")
        paper['number'] = entry.get('number', "")
        paper['author'] = entry['author']
        # TODO abstract

        # 查看会议的索引因子等信息
        journal = detailJournal(paper['journal'])
        paper['journal_h-index'] = journal.get('h-index', "")
        paper['journal_CiteScore'] = journal.get('CiteScore', "")
        paper['journal_area'] = journal.get('area', "")

        idx += 1
        papers.append(paper)
    return papers


def detailJournal(journal):
    form_data['searchname'] = journal

    resp_search = requests.post(letpub_search_url, data=form_data, headers=headers)
    bs_journal = BeautifulSoup(resp_search.text, 'html.parser')
    raw_journal = bs_journal.select('.table_yjfx tr')
    journal = {}
    if len(raw_journal) >= 4 and len(raw_journal[2].select('td')) > 5:
        raw_journal_items = raw_journal[2].select('td')
        journal["ISSN"] = raw_journal_items[0].text
        journal["name"] = raw_journal_items[1].select('a')[0].text
        journal["score"] = raw_journal_items[2].text.replace("\n", "")
        item4_str = raw_journal_items[3].text
        print(item4_str)
        item4_str = item4_str.split("C")
        journal["h-index"] = re.search(r"\d+", item4_str[0]).group()
        journal["CiteScore"] = re.search(r"\d+\.?\d+", item4_str[1]).group()
        journal["area"] = raw_journal_items[4].text
        journal["period"] = raw_journal_items[9].text

    return journal


@deprecated
def save2csv(papers, start):
    # papers_df = pd.DataFrame(papers)
    # papers_df.to_csv("papers-" + datetime.now().isoformat(timespec='minutes').replace(":", "-") + ".csv")
    with open("papers.csv", 'a', encoding="utf-8") as writer:
        has_header = False
        for paper in papers:
            if not has_header:
                writer.write(",paper_id,paper_url,paper_name,keyword_loc_content,cite_num,journal,year,pages,volume,"
                             "number,author,journal_h-index,journal_CiteScore,journal_area\n")
                has_header = True
            writer.write("%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                start, paper['paper_id'], paper['paper_url'], paper['paper_name'], paper['keyword_loc_content'],
                paper['cite_num'], paper['journal'], paper['year'], paper['pages'], paper['volume'], paper['number'],
                paper['author'], paper['journal_h-index'], paper['journal_CiteScore'], paper['journal_area']
            ))


def save2csv_v2(papers):
    papers_df = pd.DataFrame(papers)
    papers_df.to_csv("papers-" + datetime.now().isoformat(timespec='minutes').replace(":", "-") + ".csv")


def clawPages(key_word="VNF", start_year=2019, end_year=2022, pages=25, start=0):

    big_papers = []
    for i in range(pages):
        _scholar_url = scholar_url % (start, key_word, start_year, end_year)
        papers = clawOnePage(_scholar_url, start)
        big_papers.extend(papers)
        start += 10
        time.sleep(20)
    save2csv_v2(big_papers)


def printLogo():
    with open('npu cs226_logo.txt', 'r') as reader:
        lines = reader.readlines()

        for line in lines:
            for c in line:
                if c == ' ':
                    print("\033[0;42;32m \033[0m", end="")
                else:
                    print(" ", end="")
            print()


if __name__ == '__main__':
    printLogo()
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", "-kw", required=True, help="indicates what you want to search in google "
                                                                "scholar website. if it has spaces, please use "
                                                                "quotation marks, eg. \"network slice\"")
    parser.add_argument("--range", "-r", help="The time range of searching.", default="2019-2022")
    parser.add_argument("--pages", "-p", help="The number of pages crawled.", default=2, type=int)
    parser.add_argument("--start", "-s", help="The first page.", default=1, type=int)
    parser.add_argument("--enable", "-e", default=True, action="store_true", help="Using mirror or not.")
    parser.add_argument("--mirror", "-m", default="xs.studiodahu.com", help="Specifying a mirror, it can be found "
                                                                                "in website: http://scholar.scqylaw"
                                                                                ".com/. eg. xueshu.studiodahu.com")
    args = parser.parse_args()
    years = args.range.split("-")
    start_y = years[0]
    end_y = years[1]
    if args.mirror:
        scholar_url = scholar_url.replace("scholar.google.com.hk", args.mirror)
        cite_url = cite_url.replace("scholar.google.com.hk", args.mirror)

    clawPages(key_word=args.keyword, pages=args.pages, start_year=start_y, end_year=end_y, start=args.start)
