#
# Copyright 2022 Duncan Rose
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from logging import getLogger

logger = getLogger(__name__)

class ValueMixin:
    """Mixin for sheets that have a value.

    If the value associated with a ValueMixin is updated using the
    "set_value" method and the mixin has an "on_value_changed"
    attribute, the "on_value_changed" attribute will be invoked as a
    callback taking parameters "from_value" and "to_value" for the
    previous value and the new value respectively.

    """
    def __init__(self,
                 value=None,
                 on_value_changed=None):
        self._value = value
        if on_value_changed is None:
            self.on_value_changed = self.default_on_value_changed
        else:
            self.on_value_changed = on_value_changed

    def default_on_value_changed(self, from_value=None, to_value=None):
        pass

    def value(self):
        return self._value

    def set_value(self, value):
        from_value = self._value
        if from_value != value:
            self._value = value
            if hasattr(self, "on_value_changed"):
                self.on_value_changed(from_value=from_value, to_value=self._value)
