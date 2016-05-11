from WhatApi import get_requests_soup, parse_requests_page, UserSession,\
    get_login


u_name, pw = get_login()
# u_name = credentials[0]
# pw = credentials[1]

user = UserSession(user_name=u_name, password=pw)
soup = get_requests_soup(user)
page_results = parse_requests_page(soup)

for i in page_results:
    print(i)
