from Models import query_all_requests, Session, organize_data_model
from WhatApi import UserSession, get_login, similar, GazelleAPIMod, \
    get_requests_soup, parse_requests_page

u_name, pw = get_login()
user = UserSession(user_name=u_name, password=pw)


def update_album_requests():
    exists = False
    pages = list(range(1, 1000))
    for page in pages:
        soup = get_requests_soup(user, page=page)
        parsed_soup = parse_requests_page(soup)
        exists = organize_data_model(parsed_soup)
        if exists:
            return page


def find_matches():
    """
        Finds matches between existing Album Requests and existing
        torrents on What.cd

        Takes into account
            Artist Name
            Album Name
            Acceptable Formats (FLAC, FLAC 24, MP3)
            Acceptable Bitrates (Lossless, Lossy)
            Acceptable Media (WEB, CD)
    """

    matches = {}
    all_requests = query_all_requests()
    what_object = GazelleAPIMod(username=u_name, password=pw)

    # Query all of our requests from our stored database
    for stored_request in all_requests:
        stored_name = stored_request.name.split('-')
        artist = stored_name[0].strip()
        album = stored_name[1].strip()
        req_id = stored_request.id
        request_object = what_object.request_search_by_id(req_id)

        # Query API with artist name - returns all existing artist material
        artist_query = what_object.get_artist_json(artist)
        # torrentgroup keyword filters just torrents, removing metadata
        torrent_groups = artist_query.get('torrentgroup', [])
        # artist_id = artist_query['id']

        # Iterate over torrent groups
        for torrent_group in torrent_groups:
            torrent_group_album = torrent_group['groupName']
            if similar(album, torrent_group_album) > 0.8:
                matches[request_object] = [torrent_group]

                _format = set(request_object.acceptable_formats)
                bitrate = set(request_object.acceptable_bitrates)
                media = set(request_object.acceptable_media)

                # Iterate individual torrents
                for tor in torrent_group['torrent']:
                    tor_format = tor['format']
                    tor_media = tor['media']
                    # tor_bitrate = tor['encoding']
                    tor_id = tor['id']

                    if _format.intersection(set(tor_format)) or \
                            media.intersection(set(tor_media)):
                        package = (req_id, tor_id)
                        matches[request_object].append(package)

    return matches


if __name__ == '__main__':
    page_num = update_album_requests()
    print(page_num)
