# -*- coding: utf-8 -*-
#
#  Copyright 2018 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CIMM (ChemoInformatics Models Manager).
#
#  CIMM is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from collections import Counter
from pickle import dumps, loads
from uuid import uuid4


def update_chunks(chunks, job, redis, size, ttl):
    partial_chunk = next((c_id for c_id, fill in Counter(chunks.values()).items() if fill < size), None)
    model = job.meta['model']

    loaded_chunks = {}
    for s in job.result:
        results = dict(results=s.pop('results', []), model=model)
        s_id = s['structure']
        if s_id in chunks:
            c_id = chunks[s_id]
            ch = loaded_chunks.get(c_id) or loaded_chunks.setdefault(c_id, loads(redis.get(c_id)))
            ch[s_id]['models'].append(results)
        else:
            if partial_chunk:
                ch = loaded_chunks.get(partial_chunk) or \
                     loaded_chunks.setdefault(partial_chunk, loads(redis.get(partial_chunk)))
            else:
                partial_chunk = str(uuid4())
                ch = loaded_chunks[partial_chunk] = {}

            s['models'] = [results]
            ch[s_id] = s
            chunks[s_id] = partial_chunk

            if len(ch) == size:
                partial_chunk = None

    for c_id, chunk in loaded_chunks.items():
        redis.set(c_id, dumps(chunk), ex=ttl)
