from Models import query_all_requests, organize_data_model
from WhatApi import get_login, similar, GazelleAPIMod, \
    get_requests_soup, parse_requests_page, match_two_sets, \
    filter_torrent_alphabetically

u_name, pw = get_login()


# user = UserSession(user_name=u_name, password=pw)


def update_album_requests():
    exists = False
    pages = list(range(1, 1000))
    for page in pages:
        soup = get_requests_soup(page=page)
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
    what_object = GazelleAPIMod(username=u_name, password=pw)
    # Query all of our requests from our stored database
    all_requests = [(x.id, x.name) for x in query_all_requests() if
                    x.name.find('-') >= 0]

    for req_id, full_name in all_requests:
        name_part = full_name.split('-')
        artist = name_part[0].strip()
        album = name_part[1].strip()
        request_object = what_object.request_search_by_id(req_id)

        # Query API with artist name - returns all existing artist material
        artist_data = what_object.get_artist_json(artist)
        # torrentgroup keyword filters just torrents, removing metadata
        torrent_groups = artist_data.get('torrentgroup', [])
        # artist_id = artist_query['id']
        filtered_groups = filter_torrent_alphabetically(torrent_groups, album)
        # Iterate over torrent groups
        for torrent_group in filtered_groups:
            torrent_group_album = torrent_group['groupName']
            if similar(album, torrent_group_album, threshold=0.8):
                matches[request_object] = [torrent_group]

                # bitrate = set(request_object.acceptable_bitrates)
                _format = set(request_object.acceptable_formats)
                media = set(request_object.acceptable_media)

                # Iterate individual torrents
                for tor in torrent_group['torrent']:
                    tor_format = tor['format']
                    tor_media = tor['media']
                    # tor_bitrate = tor['encoding']
                    tor_id = tor['id']

                    format_match = match_two_sets(set(tor_format), _format)
                    media_match = match_two_sets(media, set(tor_media))

                    if format_match and media_match:
                        package = (req_id, tor_id)
                        with open('matches.txt', 'a+') as f:
                            f.write("Request Id: {}\nTorrent Id: {}\n\n"
                                    .format(package[0], package[1]))

    return matches


if __name__ == '__main__':
    find_matches()
    # update_album_requests()
