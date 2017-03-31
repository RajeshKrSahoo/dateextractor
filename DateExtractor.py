# coding: utf-8
import copy
import logging
import regex as re
from dateutil import tz, parser
from datetime import date
import itertools
import datetime
class DateFinder(object):

    DIGITS_MODIFIER_PATTERN = '\d+st|\d+th|\d+rd|first|second|third|fourth|fifth|sixth|seventh|eighth|nineth|tenth|next|last'
    DIGITS_PATTERN = '\d+'
    DAYS_PATTERN = 'monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thur|thurs|fri|sat|sun'
    MONTHS_PATTERN = 'january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec'
    DELIMITERS_PATTERN = '[/\:\-\,\’\s\_\+\@]+'
    EXTRA_TOKENS_PATTERN = 'till date|present'

    DATES_PATTERN = """
    (
        (
            ## Grab any digits
            (?P<digits_modifier>{digits_modifier})
            |
            (?P<digits>{digits})
            |
            (?P<months>{months})
            |
            (?P<delimiters>{delimiters})
            | 
            (?P<extra_tokens>{extra_tokens})
        ){{3,}}
    )
    """
    MULTIPLE_DATE_PATTERN = """

    """
    DATES_PATTERN = DATES_PATTERN.format(
        digits=DIGITS_PATTERN,
        digits_modifier=DIGITS_MODIFIER_PATTERN,
        days=DAYS_PATTERN,
        months=MONTHS_PATTERN,
        delimiters=DELIMITERS_PATTERN,
        extra_tokens=EXTRA_TOKENS_PATTERN
    )
    REPLACEMENTS = {
        "’": " ",
        "'": " ",
        "`": " ",
        
    }
    DATE_REGEX = re.compile(DATES_PATTERN, re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL | re.VERBOSE)
    STRIP_CHARS = ' \n\t:-.,_'

    def __init__(self, base_date=None):
        self.base_date = base_date

    def find_dates(self, text, source=False, index=False):
        date_list = []
        text = re.sub('present|till date', 'to'+ date.today().strftime('%d/%m/%Y'), text, re.IGNORECASE)
        for date_string, indices, captures in self.extract_date_strings(text):

            as_dt = self.parse_date_string(date_string, captures)
            if as_dt is None:
                continue

            returnables = (as_dt,)
            if source:
                returnables = returnables + (date_string,)
            if index:
                returnables = returnables + (indices,)

            if len(returnables) == 1:
                returnables = returnables[0]
            date_list.append(returnables)
        return date_list

    def _find_and_replace(self, date_string, captures):
        for key, value in self.REPLACEMENTS.items():
            date_string = date_string.replace(key, value)
        return date_string
    def parse_date_string(self, date_string, captures):
        try:
            as_dt = parser.parse(date_string, default=self.base_date)
        except ValueError:
            date_string = self._find_and_replace(date_string, captures)
            # print date_string

            date_string = date_string.strip(self.STRIP_CHARS)
            if len(date_string) < 3:
                return None

            try:

                as_dt = parser.parse(date_string, default=self.base_date)
            except Exception as e:
                as_dt = None
        return as_dt

    def add_period_delimiter(self, text):
        for match in self.DATE_REGEX.finditer(text):
            match_str = match.group(0)
            indices = match.span(0)
            captures = match.capturesdict()
            digits = captures.get('digits')
            # print digits
            digits_modifiers = captures.get('digits_modifiers')
            months = captures.get('months')
            delimiters = captures.get('delimiters')
            extra_tokens = captures.get('extra_tokens')
            prev = 0
            try:
                if len(months) == 2 or len(digits) > 3 or len(digits_modifiers) > 1:
                    

                    mid = (indices[1]+indices[0])/2 + 1
                    
                    if len(months) == 2:
                        month_with_smallest_length = min(months, text.rindex)
                        diff = len(months[0]) - len(months[1])
                        if len(months[0]) > len(months[1]):
                            mid = mid + abs(diff)
                        if len(months[0]) < len(months[1]):
                            mid = mid - abs(diff)
                    # print mid

                    for string in itertools.chain(digits, months):
                        # print string
                        curr_end_idx = text.rindex(string) + len(string)
                        if  curr_end_idx <= mid and curr_end_idx > prev:
                            prev = curr_end_idx
                    text = text[: prev] + ' to ' + text[prev: ]
            except Exception as e:
                # print e
                pass
        return text
    
    def extract_date_strings(self, text):
        text = self.add_period_delimiter(text)
        for match in self.DATE_REGEX.finditer(text):
            match_str = match.group(0)
            indices = match.span(0)
            captures = match.capturesdict()
            digits = captures.get('digits')
            # print digits
            digits_modifiers = captures.get('digits_modifiers')
            months = captures.get('months')
            delimiters = captures.get('delimiters')
            extra_tokens = captures.get('extra_tokens')
            match_str = re.sub('[\n\t\s\xa0]+', ' ', match_str)
            match_str = match_str.strip(self.STRIP_CHARS)
            yield match_str, indices, captures
    
    @staticmethod
    def get_period(datetime1, datetime2, in_days = False, in_years = True):
        diff = datetime2 - datetime1
        if in_days:
            return diff.days
        return diff.days/364.5


if __name__ == '__main__':

    # return date_finder.find_dates(text)

    dates = [
        'worked from 10 may 00 to present and dasdsad',
        '10/July',
        'July/99 to July/99',
        '10/2016',
        '10/16',
        '10-July-00',
        '10-July 00 - 1-June 02',
        'July-2017',
        '10 July, 2000',
        '10th July, 2000',
        'July, 2000',
        "July’15",
        '04 2000 02 2001',
        'April 2014',
        ]

    # print map(DateFinder(base_date=datetime.datetime(2000, 01, 01, 0, 0)).find_dates, dates)
    # print DateFinder.get_period(*DateFinder(base_date=datetime.datetime(2000, 01, 01, 0, 0)).find_dates(dates[0]))
    df = DateFinder(base_date=None)
    dates = df.find_dates("worked from 22nd october 2001 to 12th may 2003")
    print 'period(years): ', DateFinder.get_period(*dates)
    dates = df.find_dates("worked from oct 2002 to nov 2003")
    print 'period(years): ', DateFinder.get_period(*dates)
    dates = df.find_dates("oct 2002 - nov 2003")
    print 'period(years): ', DateFinder.get_period(*dates)
    dates = df.find_dates("12/12/2002 - 12/12/2003")
    print 'period(years): ', DateFinder.get_period(*dates)
# print map(list,map(find_dates, dates))





