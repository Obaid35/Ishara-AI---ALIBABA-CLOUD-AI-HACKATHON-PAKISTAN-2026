# Content Permission Request

## Tracking

Fill this in when the request is sent. An untracked request is indistinguishable from one never sent — and this is a High-impact risk due on Day 1.

| Field | Value |
|---|---|
| Recipient organisation | |
| Recipient contact | |
| Sent by | |
| Sent on | |
| Method | email / form / other |
| Status | `not_sent` / `sent` / `responded` / `granted` / `denied` |
| Response received on | |
| Conditions attached | |
| Evidence filed at | |

Mirror the outcome into `asset_rights` for every affected asset ([Data Model](DATA_MODEL.md)). A phrase whose video lacks demo-playback permission **cannot be enabled** — the database enforces it (invariant I2).

## Draft message

**Subject:** Permission to Use Selected PSL Videos in Student Hackathon Prototype

Hello,

We are a student team building a small healthcare accessibility prototype for a hackathon. The project aims to help a Deaf PSL user communicate basic medical needs with an Urdu-speaking doctor.

We are using Pakistan Sign Language resources to learn and verify a limited set of signs. We would also like permission to use a small number of selected PSL video clips as reference material during development and, if permitted, to display selected verified clips in the Doctor → Patient part of our prototype.

The project is non-commercial at the hackathon stage, we will clearly credit the source, and we will only use the minimum number of clips required. We do not store any patient data, and the prototype is not a diagnostic tool.

Could you please confirm whether we may use selected PSL video clips for:

1. development and testing of the hackathon prototype; and
2. playback inside the prototype and demo for selected doctor-to-patient phrases?

We are happy to follow any attribution or usage conditions you require, and we would also welcome any guidance on the accuracy of the signs we have selected.

Thank you.

_(name, team, institution, contact)_

## Note on scope

The request deliberately asks about **two separate usages**, because they are separate permissions: using a clip as a development reference is not the same as displaying it to a patient. Public release is not requested at this stage and must not be assumed if permission is granted for the two above.
