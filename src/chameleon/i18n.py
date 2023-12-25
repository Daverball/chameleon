##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import re
import typing as t

from chameleon.exc import CompilationError


NAME_RE = r"[a-zA-Z][-a-zA-Z0-9_]*"

WHITELIST = frozenset([
    "translate",
    "domain",
    "context",
    "target",
    "source",
    "attributes",
    "data",
    "name",
    "mode",
    "xmlns",
    "xml",
    "comment",
    "ignore",
    "ignore-attributes",
])

_interp_regex = re.compile(r'(?<!\$)(\$(?:(%(n)s)|{(%(n)s)}))'
                           % ({'n': NAME_RE}))

# BBB: The ``fast_translate`` function here is kept for backwards
# compatibility reasons. Do not use!

try:  # pragma: no cover
    from zope.i18n import interpolate
    from zope.i18n import translate
    from zope.i18nmessageid import Message
except ImportError:   # pragma: no cover
    pass
else:   # pragma: no cover
    def fast_translate(
        msgid: t.Optional[str],
        domain: t.Optional[str] = None,
        mapping: t.Optional[t.Mapping[str, object]] = None,
        context: t.Optional[str] = None,
        target_language: t.Optional[str] = None,
        default: t.Optional[str] = None
    ) -> t.Optional[str]:

        if msgid is None:
            return None

        if target_language is not None or context is not None:
            result = translate(
                msgid, domain=domain, mapping=mapping, context=context,
                target_language=target_language, default=default)
            if result != msgid:
                return result  # type: ignore[no-any-return]

        if isinstance(msgid, Message):
            default = msgid.default
            mapping = msgid.mapping

        if default is None:
            default = str(msgid)

        if not isinstance(default, str):
            return default

        return interpolate(default, mapping)  # type: ignore[no-any-return]


def simple_translate(
    msgid: str,
    domain: t.Optional[str] = None,
    mapping: t.Optional[t.Mapping[str, object]] = None,
    context: t.Optional[str] = None,
    target_language: t.Optional[str] = None,
    default: t.Optional[str] = None
) -> str:

    if default is None:
        default = getattr(msgid, "default", msgid)

    if mapping is None:
        mapping = getattr(msgid, "mapping", None)

    if mapping:
        def replace(match: t.Match[str]) -> str:
            whole, param1, param2 = match.groups()
            return str(mapping.get(param1 or param2, whole))
        return _interp_regex.sub(replace, default)

    return default


def parse_attributes(attrs, xml=True):
    d = {}

    # filter out empty items, eg:
    # i18n:attributes="value msgid; name msgid2;"
    # would result in 3 items where the last one is empty
    attrs = [spec for spec in attrs.split(";") if spec]

    for spec in attrs:
        if ',' in spec:
            raise CompilationError(
                "Attribute must not contain comma. Use semicolon to "
                "list multiple attributes", spec
            )
        parts = spec.split()
        if len(parts) == 2:
            attr, msgid = parts
        elif len(parts) == 1:
            attr = parts[0]
            msgid = None
        else:
            raise CompilationError(
                "Illegal i18n:attributes specification.", spec)
        if not xml:
            attr = attr.lower()
        attr = attr.strip()
        if attr in d:
            raise CompilationError(
                "Attribute may only be specified once in i18n:attributes",
                attr)
        d[attr] = msgid

    return d
