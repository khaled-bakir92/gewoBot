# Formular-Selektoren für application_bot.py

Dieses Dokument listet alle exakten Formular-Selektoren auf, die aus `appli.html` extrahiert wurden.

## ✅ Implementierte Felder (mit exakten IDs)

### Persönliche Daten

1. **Anrede** (Pflichtfeld)
   - Element: ng-select Dropdown
   - ID: `#salutation-dropdown`, `#salutation`
   - formcontrolname: `salutation`
   - Optionen: "Frau", "Herr", "Keine"
   - user_data.json Key: `personal_info.anrede`

2. **Vorname** (Pflichtfeld)
   - Element: Input
   - ID: `#firstName`
   - formcontrolname: `firstName`
   - user_data.json Key: `personal_info.vorname`

3. **Nachname** (Pflichtfeld)
   - Element: Input
   - ID: `#lastName`
   - formcontrolname: `lastName`
   - user_data.json Key: `personal_info.nachname`

4. **E-Mail** (Pflichtfeld)
   - Element: Input
   - ID: `#email`
   - formcontrolname: `email`
   - user_data.json Key: `personal_info.email`

5. **Telefonnummer** (Optional)
   - Element: Input
   - ID: `#phone-number`
   - formcontrolname: `phoneNumber`
   - user_data.json Key: `personal_info.telefon`

### Adresse

6. **Straße** (Optional)
   - Element: Input
   - ID: `#street`
   - formcontrolname: `street`
   - user_data.json Key: `personal_info.strasse`

7. **Hausnummer** (Optional)
   - Element: Input
   - ID: `#house-number`
   - formcontrolname: `houseNumber`
   - user_data.json Key: `personal_info.hausnummer`

8. **PLZ** (Optional)
   - Element: Input
   - ID: `#zip-code`
   - formcontrolname: `zipCode`
   - user_data.json Key: `personal_info.plz`

9. **Stadt** (Optional)
   - Element: Input
   - ID: `#city`
   - formcontrolname: `city`
   - user_data.json Key: `personal_info.stadt`

### Anfrage-Informationen

10. **Für wen wird die Wohnungsanfrage gestellt?** (Pflichtfeld)
    - Element: ng-select Dropdown
    - ID: `#formly_10_select_gewobag_fuer_wen_wird_die_wohnungsanfrage_gestellt_0_select`
    - Alternative ID: `#formly_10_select_gewobag_fuer_wen_wird_die_wohnungsanfrage_gestellt_0`
    - Wrapper ID: `#formly_10_select_gewobag_fuer_wen_wird_die_wohnungsanfrage_gestellt_0_wrapper`
    - Label for: `formly_10_select_gewobag_fuer_wen_wird_die_wohnungsanfrage_gestellt_0`
    - Optionen: "Für mich selbst", "Für eine andere Person/einen Dritten"
    - user_data.json Key: `personal_info.fuer_wen_anfrage`

## ⚠️ Felder mit generischen Selektoren (nicht in appli.html gefunden)

Diese Felder verwenden noch Fallback-Selektoren, da keine exakten IDs gefunden wurden:

11. **Anzahl Erwachsene**
    - Selektor: `input[placeholder*="Erwachsene"], input[id*="erwachsen"], input[name*="adult"]`
    - user_data.json Key: `household.anzahl_personen`

12. **Anzahl Kinder**
    - Selektor: `input[placeholder*="Kinder"], input[id*="kinder"], input[name*="child"]`
    - user_data.json Key: `household.anzahl_kinder`

13. **WBS vorhanden?**
    - Selektor: `input[type="radio"][value="ja"]`, `input[type="radio"][value="nein"]`
    - user_data.json Key: `household.wbs_vorhanden`

14. **Anmerkungen/Nachricht**
    - Selektor: `textarea[placeholder*="Anmerkungen"], textarea[id*="anmerkung"], textarea[name*="message"]`
    - user_data.json Key: `nachricht`

15. **Datenschutz-Checkboxen**
    - Selektor: `input[type="checkbox"]` (alle)
    - Werden automatisch aktiviert

## 📝 Hinweise

- Alle IDs mit `#` sind exakte ID-Selektoren aus dem HTML
- ng-select Dropdowns erfordern:
  1. Klick auf das Dropdown-Element
  2. Klick auf die gewünschte Option via `span.ng-option-label:has-text("...")`
- Die generischen Selektoren funktionieren als Fallback, sollten aber bei Gelegenheit durch exakte IDs ersetzt werden
- FormControlName-Attribute sind Angular-spezifisch und werden zur Identifikation verwendet

## 🔄 Aktualisierung

Wenn sich die Formularstruktur ändert:
1. Öffnen Sie das Formular im Browser
2. Inspizieren Sie die Elemente
3. Aktualisieren Sie die IDs in `application_bot.py`
4. Aktualisieren Sie dieses Dokument
