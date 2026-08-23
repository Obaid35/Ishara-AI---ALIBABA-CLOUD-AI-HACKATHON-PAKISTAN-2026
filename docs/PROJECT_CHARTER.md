# Project Charter

## Name

**PSL Bridge**

## Problem

A Deaf PSL user may reach a clinic or hospital where the doctor, nurse, or receptionist does not understand Pakistan Sign Language. Basic communication can then depend on a family member, interpreter, writing, or improvised gestures.

PSL Bridge targets a **small, defined set of healthcare interactions**.

## Vision

A Deaf patient signs in front of a normal camera and the system communicates the supported meaning to medical staff in Urdu text and Urdu speech. The doctor can respond through a small set of verified medical questions shown back to the patient in PSL video.

## Primary users

- Deaf patient — **never requires an account**
- Doctor / nurse / medical staff — signs in
- Administrator — manages verified content

## Primary use cases

- pain or symptom communication;
- fever/cough;
- breathing difficulty;
- dizziness;
- bleeding/injury;
- duration;
- yes/no;
- help/medicine needs.

## Product boundary

PSL Bridge is a **communication assistant**, not a diagnosis tool, treatment system, hospital-management system, or complete PSL translator. Complex or high-risk conversations may still require a qualified interpreter.

There are no patient records, no appointments, and no stored consultation transcripts.

## Core success

A new signer can use the live camera to produce a supported medical message, confirm it visually, and make the laptop speak correct Urdu; the doctor can send back a small set of verified PSL responses — **all without internet, and without the patient logging in.**

## Reliability philosophy

- Unknown is better than confidently wrong.
- 15 verified reliable signs beat 40 shaky signs.
- New-person testing matters more than source-video accuracy.
- The exact live demo should work **9/10 times** before presentation.
- No single dependency may kill the demo.

## Scope targets

### Minimum (Tier A — never cut)
- 15 reliable signs
- 10 patient messages
- 10 doctor PSL responses
- Urdu text + Urdu voice from pre-generated local audio
- live camera, no patient login
- retry/unknown
- confirm-before-speak
- unseen-person testing
- runs fully offline

### Target
- 20–30 reliable signs
- 15 patient messages
- 15 doctor responses
- PostgreSQL content store with enforced invariants
- staff login and roles (Tier B)
- admin console for verified content (Tier C)

### Stretch
- 30–40 reliable signs
- English text and speech toggle
- doctor Urdu voice input selecting verified phrases
- visual tracking overlay

## Governing constraint

The application may grow a login, an admin console and a database. **None of that outranks a working recognizer validated on someone who has never used the system.** Build order and cut order both follow from that.
