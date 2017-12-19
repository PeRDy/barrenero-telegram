import datetime


def humanize_iso_date(d):
    return datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y %H:%M")
