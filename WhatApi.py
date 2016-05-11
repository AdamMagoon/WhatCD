from bs4 import BeautifulSoup
from pygazelle.pygazelle import api
from requests import Session

u_name = 'FilthyFingers'
pw = '2016Platinum'
what_object = api.GazelleAPI(username=u_name, password=pw)
requests_page = 'https://what.cd/requests.php'


class UserSession(Session):
    login_page = 'https://what.cd/login.php'

    new_headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 6.3; WOW64;\
         Trident/7.0; MALNJS; rv:11.0) like Gecko",
        'Accept-Encoding': ', '.join(('gzip', 'deflate')),
        'Accept': '*/*',
        'Connection': 'keep-alive',
    }

    def __init__(self, user_name, password):
        super().__init__()
        self.user_name = user_name
        self.password = password
        self.headers = self.new_headers

        auth = {'username': self.user_name, 'password': self.password,
                'keeplogged': 1, 'login': 'Log in'}
        self.post(self.login_page, data=auth)


class AlbumRequest:
    def __init__(self, name, _id, tags, votes, bounty, filled, filled_by,
                 requested_by, created_date, last_vote):
        self.name = name
        self.id = _id
        self.tags = tags
        self.votes = votes
        self.bounty = bounty
        self.filled = filled
        self.filled_by = filled_by
        self.requested_by = requested_by
        self.created_date = created_date
        self.last_vote = last_vote

    def __repr__(self):
        return """
name = {}
id = {}
tags = {}
votes = {}
bounty = {}
filled = {}
date = {}
""".format(self.name, self.id, self.tags, self.votes,
           self.bounty, self.filled, self.created_date)


def get_requests_soup(session):
    response = session.get(requests_page)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup


def parse_requests_page(soup):
    """ Given a BeautifulSoup Tag object, we return a list of
        AlbumRequest objects.

    """
    results = []
    table_soup = soup.find('table', {'id': 'request_table'})
    # This is currently the <a></a> tag's href snippet for accessing the
    # request ID's page
    request_key = 'requests.php?action=view&id='

    # List of table row tags <tr></tr>
    table_rows = table_soup.find_all('tr')

    for row in table_rows[1::]:
        # List of only the text from the table columns in this row <td></td>
        column = [x.text.strip() for x in row.find_all('td')]

        # List of href attribute contents from all anchor tags in this row
        hrefs = [x['href'] for x in row.find_all('a')]

        # We get the Album Request id by selecting the anchor tag which
        # uses our request_key variable. When we find this we know the
        # remaining 6 characters are the Album Request id we are looking for.
        id_tag = [x for x in hrefs if request_key in x][0]

        # We isolate the id by selecting the last 6 characters of the string
        _id = id_tag[-6::]

        # Media tags are kept in a separate div within the table column tag
        # with the format:
        # <div class="tags">....</div>
        tags = row.find_all('div', attrs={'class': 'tags'})[0].text.strip()

        # Random '\n' tags seem to be popping up within the text even after
        # striping them. using replace() is a "just-in-case" precaution
        # -1 will allow all occurrences of '\n' to be replaced.
        name = column[0].replace('\n', '', -1)

        # the HTML for the votes tag contains two elements. We only need the
        # first -- the number of votes.
        votes = column[1][0]

        bounty = column[2]
        filled = column[3]
        f_by = column[4]
        req = column[5]
        created = column[6]
        last_vote = column[7]

        # Finally we initialize our AlbumRequest instance
        new_request = AlbumRequest(name, _id, tags, votes, bounty, filled, f_by,
                                   req, created, last_vote)

        # And add it to our results
        results.append(new_request)

    # Return results list of AlbumRequest instances
    return results


def get_login():
    with open('secret.txt', 'r') as f:
        lines = [line.strip() for line in f]
        username = lines[0]
        password = lines[1]

    return username, password
