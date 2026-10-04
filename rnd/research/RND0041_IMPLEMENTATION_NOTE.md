# RND-0041 Implementation Note

The validation acquisition wrapper reuses the existing GET-only OANDA PRACTICE quarantine engine with one exact cross-year shard identity:

- label: `validation-2021-2022`
- start inclusive: `2020-12-31T19:15:00Z`
- end exclusive: `2023-01-01T09:40:00Z`

The label is metadata only. Request planning and boundary enforcement are driven by the exact UTC start/end values.

The wrapper fail-closes unless RND-0041 is separately activated for acquisition. Current repository declaration is deliberately inactive.

No strategy evaluation, candidate evaluation, validation scoring or reserved-final access is implemented or authorized by this wrapper.
