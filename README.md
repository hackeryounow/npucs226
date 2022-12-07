# npucs226
- Before using it, please install some dependencies
    ```shell
    pip install -r requirements.txt
    ````
- Using `python ./clawer.py -h` for directions
    ```shell
    usage: clawer.py [-h] --keyword KEYWORD [--range RANGE] [--pages PAGES] [--start START] [--enable] [--mirror MIRROR]
    
    optional arguments:
      -h, --help            show this help message and exit
      --keyword KEYWORD, -kw KEYWORD
                            indicates what you want to search in google scholar website. if it has spaces, please use quotation marks, eg. "network slice"
      --range RANGE, -r RANGE
                            The time range of searching.
      --pages PAGES, -p PAGES
                            The number of pages crawled.
      --start START, -s START
                            The first page.
      --enable, -e          Using mirror or not.
      --mirror MIRROR, -m MIRROR
                            Specifying a mirror, it can be found in website: http://scholar.scqylaw.com/. eg. xueshu.studiodahu.com
    
    ```
- One simple example, I want to search some papers about VNF, and only 2 papges, excuting below command:
    ```shell
    python .\clawer.py  -kw "VNF" -p 2
    ```