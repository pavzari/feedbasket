from datetime import datetime


def display_publication_date(date):

    if date is None:
        return ""

    delta = datetime.utcnow() - date

    if delta.total_seconds() < 60:
        return f"{delta.seconds}s ago"
    elif delta.total_seconds() < 3600:
        minutes = delta.seconds // 60
        return f"{minutes}min ago"
    elif delta.days == 0:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.days < 365:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    else:
        return date.strftime("%b %Y")
