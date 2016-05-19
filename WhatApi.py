from re import sub
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from pygazelle import pygazelle
from pygazelle.pygazelle import api, request
from pygazelle.pygazelle.request import InvalidRequestException
from requests import Session
from time import time, sleep
from requests import get

# what_object = GazelleAPIMod(username=u_name, password=pw)
requests_page = 'https://what.cd/requests.php/'

def rate_limiter(max_per_10_seconds):
    min_interval = 10.0 / float(max_per_10_seconds)

    def decorate(func):
        last_time_called = [0.0]

        def rate_limited_function(*args, **kwargs):
            elapsed = time() - last_time_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                print("Sleeeep....")
                sleep(left_to_wait)
                print("Okay, wake up!")
            ret = func(*args, **kwargs)
            last_time_called[0] = time()
            return ret
        return rate_limited_function
    return decorate


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


class RequestMod(request.Request):

    def __init__(self, id, parent_api):
        self.id = id
        self.parent_api = parent_api
        self.category = None
        self.title = None
        self.year = None
        self.time_added = None
        self.votes = None
        self.bounty = None
        self.album_title = None
        self.acceptable_media = None
        self.acceptable_bitrates = None
        self.acceptable_formats = None
        self.description = None
        self.tags = None
        self.artist = None
        self.name = None

        self.parent_api.cached_requests[
            self.id] = self  # add self to cache of known Request objects

    def set_data(self, request_item_json_data):
        if self.id != request_item_json_data['requestId']:
            raise InvalidRequestException(
                "Tried to update a Request's information from a request JSON item with a different id." +
                " Should be %s, got %s" % (
                self.id, request_item_json_data['requestId']))
        self.category = self.parent_api.get_category(
            request_item_json_data['categoryId'])
        self.album_title = request_item_json_data['title']
        self.year = request_item_json_data['year']
        self.time_added = request_item_json_data['timeAdded']
        self.votes = request_item_json_data['voteCount']
        self.bounty = request_item_json_data['totalBounty']
        self.acceptable_bitrates = request_item_json_data['bitrateList']
        self.acceptable_formats = request_item_json_data['formatList']
        self.acceptable_media = request_item_json_data['mediaList']
        self.description = request_item_json_data['description']
        self.tags = request_item_json_data['tags']
        music_info = request_item_json_data['musicInfo']
        if 'artists' in music_info.keys():
            self.artist = music_info['artists'][0]['name']
            self.name = "{} - {}".format(self.artist, self.album_title)
        self.parent_api.cached_requests[self.id] = self

    def __repr__(self):
        return "Request: %s - ID: %s" % (self.album_title, self.id)


class GazelleAPIMod(api.GazelleAPI):

    def torrent_search_by_artist(self, artist):
        return self.search_torrents(artistname=artist)

    def request_search_by_id(self, req_id):
        return self.get_request(req_id)

    def get_artist_json(self, artist_name):
        return self.artist_json(artist_name)

    @rate_limiter(5)
    def get_request(self, id, **kwargs):
        """
            Returns a Request for the passed ID, associated with this API object. You'll need to call Request.update_data()
            if the request hasn't already been cached. This is done on demand to reduce unnecessary API calls.
        """

        id = int(id)
        kwargs['id'] = id
        response = self.request(action='request', **kwargs)

        req = RequestMod(id, self)
        req.set_data(response)
        return req

    @rate_limiter(5)
    def artist_json(self, artist_name):
        try:
            return self.request(action='artist', artistname=artist_name)
        except pygazelle.api.RequestException as e:
            print(e)
            print("Artist Name: {}".format(artist_name))
            return self.request(action='browse', artistname=artist_name)


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
        try:
            self.id = int(_id)
        except ValueError as e:
            _id = _id.strip()
            self.id = int(_id)

        self.name = name
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


@rate_limiter(5)
def get_requests_soup(session, page=1):
    response = get(requests_page + "?page={}".format(page))
    if response.status_code != 200:
        print('Cannot make a proper connection to the server {}.\n'
              'Status Code: {}\n'
              'Exiting Program.'.format(requests_page, response.status_code))
        quit()

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
        # Double confirm that only alphanumeric characters exist in string
        _id = sub(r'[a-zA-Z=]', '', _id)

        # Media tags are kept in a separate div within the table column tag
        # with the format:
        # <div class="tags">....</div>
        tags = row.find_all('div', attrs={'class': 'tags'})[0].text.strip()

        # Random '\n' tags seem to be popping up within the text even after
        # striping them. using replace() is a "just-in-case" precaution
        # -1 will allow all occurrences of '\n' to be replaced.
        name = column[0].replace('\n', '', -1).replace(tags, '').rstrip()

        # the HTML for the votes tag contains two elements. We only need the
        # first -- the number of votes.
        votes = column[1][0]

        bounty = column[2]
        filled = column[3]

        if filled == 'No':
            filled = False
        else:
            filled = True

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
