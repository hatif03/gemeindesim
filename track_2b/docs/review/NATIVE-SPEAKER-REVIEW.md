# Native-speaker review: GemeindeSim German and French

Thank you. The authors are **not** native speakers of German or French; the sample booklet, the glossary and the
residents' lines were produced with machine assistance. This pack asks you to judge what a Swiss reader would see.

## What to do (about 45 minutes)

1. Read the **synthetic booklet** (section A) as if it were a municipal *Abstimmungsbüchlein* / *brochure de vote*.
2. Rate each numbered item (sections B and C) on the five criteria below, 1 (bad) to 5 (native-natural).
3. Write the corrected wording wherever you would change something. Mark *Germanisms* (Hochdeutsch/Germany vocabulary
   in a Swiss text, e.g. *Abitur* for *Matura*) and *Gallicisms* / France-French (e.g. *nonante* vs *quatre-vingt-dix*).
4. Return the filled `review-sheet.csv` (or this file). Items keep the same ids.

### Criteria

| code | question |
| --- | --- |
| REG | Is the register right for this person and situation (neighbour talking, official text, report)? |
| TERM | Are the official terms right (Vorlage, Steuerfuss, Gemeinderat / objet, taux d'imposition, conseil communal …)? |
| CH | Does it sound Swiss (vocabulary, *ss* instead of *ß*, number format 80'000, CHF) rather than German/French-French? |
| NAT | Would a person really say or write it this way (not stiff, not translated)? |
| ERR | Any outright error (grammar, wrong word, wrong meaning)? Quote it. |

## A. The synthetic booklet text

### Deutsch

```
Gemeinde Linden — Vorlage: Erhöhung des Steuerfusses und Schulhauskredit

Abstimmungsfrage: Wollen Sie den Steuerfuss von 118 % auf 124 % der einfachen Steuer erhöhen und einen Kredit von 4.8 Millionen CHF für den Neubau des Schulhauses Linden-Dorf annehmen?

Erläuterungen des Gemeinderats:

1. Der Steuerfuss bleibt seit 2019 bei 118 %. Die Jahresrechnung 2025 schliesst mit einem Defizit von 1.2 Millionen CHF. Ohne Massnahme müsste die Gemeinde die Rückstellungen für Strassen und Sozialhilfe kürzen.

2. Der Schulhauskredit von 4.8 Millionen CHF finanziert acht Klassenzimmer, eine Turnhalle und eine Tagesschule. Die Baukosten sind im Voranschlag 2027 enthalten. Ein Nein zum Kredit verschiebt den Bau um mindestens drei Jahre.

3. Was ein Ja ändert: Der Steuerfuss steigt um 6 Prozentpunkte. Für ein steuerbares Einkommen von 80'000 CHF bedeutet das rund 240 CHF mehr pro Jahr. Die Gemeinde kann den Schulhausbau 2027 beginnen.

4. Was ein Nein ändert: Der Steuerfuss bleibt 118 %. Das Defizit von 1.2 Millionen CHF bleibt. Der Gemeinderat müsste Sparaufträge von 400'000 CHF bei der Schule und 200'000 CHF bei den Werkhöfen vorschlagen.

5. Kleine Läden an der Dorfstrasse rechnen mit leicht höherer Nachfrage, wenn die Tagesschule Personal bindet. Baupreise für Stahl und Beton sind im Voranschlag mit +8 % gegenüber 2024 angesetzt.

Keine Abstimmungsempfehlung in diesem Auszug. Quellen: synthetische Muster-Vorlage für GemeindeSim (keine echte Gemeinde).
```

### Français

```
Commune de Linden — objet: hausse du taux d'imposition et crédit pour l'école

Question votée: Acceptez-vous de porter le taux d'imposition de 118 % à 124 % de l'impôt simple et d'accorder un crédit de 4,8 millions CHF pour la construction du nouveau bâtiment scolaire de Linden-Village?

Explications du conseil communal:

1. Le taux d'imposition est resté à 118 % depuis 2019. Les comptes 2025 se soldent par un déficit de 1,2 million CHF. Sans mesure, la commune devrait réduire les provisions pour les routes et l'aide sociale.

2. Le crédit scolaire de 4,8 millions CHF finance huit salles de classe, une salle de gymnastique et une structure d'accueil de jour. Les coûts de construction figurent au budget 2027. Un non reporterait le chantier d'au moins trois ans.

3. Ce que change un oui: le taux augmente de 6 points. Pour un revenu imposable de 80'000 CHF, cela représente environ 240 CHF de plus par an. La commune peut lancer le chantier en 2027.

4. Ce que change un non: le taux reste à 118 %. Le déficit de 1,2 million CHF demeure. Le conseil communal devrait proposer des économies de 400'000 CHF à l'école et 200'000 CHF aux services techniques.

5. Les petits commerces de la rue du village tablent sur une demande un peu plus forte si l'accueil de jour embauche. Les prix du béton et de l'acier sont budgétés +8 % par rapport à 2024.

Pas de recommandation de vote dans cet extrait. Source: objet fictif pour GemeindeSim (aucune commune réelle).
```

## B. Fixed phrases, glossary and report

| id | what | lang | context | text | REG | TERM | CH | NAT | ERR / correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | report headline | de | 70B report, German | Steuerfuss-Erhöhung und Schulhauskredit: Belastung für Haushalte, Hoffnung für Bau und Bildung |  |  |  |  |  |
| R02 | report summary | de | 70B report, German | Die Simulation zeigt, dass eine Erhöhung des Steuerfusses von 118 % auf 124 % die Kaufkraft der Haushalte belastet, während der Schulhauskredit neue Arbeitsplätze im Bausektor schafft und die Nachfrage im Einzelhandel ankurbeln könnte. Dieser Bericht gibt keine Abstimmungsempfehlung ab. |  |  |  |  |  |
| R03 | report livelihood | de | 70B report, German | Haushalte würden mit weniger verfügbarem Einkommen dastehen, da die Steuerlast steigt. Gleichzeitig könnten lokale Geschäfte von einem Zustrom neuer Kunden profitieren, wenn die Tagesschule eröffnet wird, doch die Unsicherheit über die eigene finanzielle Situation bleibt hoch. |  |  |  |  |  |
| F01 | fallback line | de | shown when the model fails twice | Ich will die amtliche Erklärung noch einmal lesen, bevor ich mich festlege. |  |  |  |  |  |
| F02 | fallback line | fr | shown when the model fails twice | Je veux relire l'explication officielle avant de me prononcer. |  |  |  |  |  |
| N-de | report disclaimer | de | appended to every vote report | Dieser Bericht gibt keine Abstimmungsempfehlung ab. |  |  |  |  |  |
| N-fr | report disclaimer | fr | appended to every vote report | Ce rapport ne recommande pas comment voter. |  |  |  |  |  |
| G-de | glossary (terms the residents are told to prefer) | de | prompt glossary | Vorlage, Abstimmungsfrage, Erläuterungen, Stimmvolk, Steuerfuss, Gemeinderat, Rechnung, Budget, Gemeinde, CHF |  |  |  |  |  |
| G-fr | glossary (terms the residents are told to prefer) | fr | prompt glossary | objet, question votée, explications, souverain, taux d'imposition, conseil communal, comptes, budget, commune, CHF |  |  |  |  |  |

## C. Residents' lines (generated; seeded sample, 14 from the 70B and 6 from the 8B per language)

| id | lang | context | text | REG | TERM | CH | NAT | ERR / correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L01 | de | 70B · tenant · freelance urban planner with a focus on sustainable housing retrofits · chat | Olivia, ich habe die Unterlagen zum Steuerfuss und zum Schulhauskredit noch einmal durchgesehen. Die 4,8 Millionen CHF für den Neubau sind nicht nur ein Gebäude, sondern ein Signal: Linden investiert in seine Zukunft. Für ein steuerbares Einkommen von 80'000 CHF sind es zwar rund 432 CHF mehr pro Jahr – aber wenn wir das Schulhaus bauen und die Infrastruktur stärken, steigt langfristig auch der Wert unserer nachhaltig sanierten Altbauten. Das ist gut für unsere Gemeinde und für unsere Arbeit als Planerin. |  |  |  |  |  |
| L02 | de | 70B · municipal_employee · Sachbearbeiterin Finanzen im Gemeindeverwaltung Linden · chat | Herr Rochat, ich habe die Vorlage zum Schulhauskredit und zur Steuererhöhung gelesen. Als Sachbearbeiterin im Finanzwesen sehe ich die Zahlen, aber ich sehe auch die Kinder, die morgen in diesen Räumen lernen werden. Die Tagesschule und die neuen Klassenzimmer sind keine Luxusausgaben, sondern eine Investition in die Zukunftsfähigkeit unserer Gemeinde. Die Erläuterungen des Gemeinderats zeigen deutlich, dass ohne diesen Schritt die Rückstellungen für Sozialhilfe und Strassen unter Druck geraten würden. Bildung ist doch die Grundlage für Chancengleichheit, nicht wahr? |  |  |  |  |  |
| L03 | de | 70B · municipal_employee · Leiter der Abteilung Finanzen und Steuern (Finance and Taxes Division) · mood_shift | Die Klagen der Ladenbesitzer und die Sorgen meiner Frau über die Klassenräume lassen mich nicht los. Ich muss einen Weg finden, die Rechnung ohne Steuererhöhung zu begleichen, bevor die Stimmung kippt. |  |  |  |  |  |
| L04 | de | 70B · farmer · Milchkuhhalterin mit Direktvermarktung · chat | Céline, ich bin hin- und hergerissen. Der Schulhausneubau bringt mehr Familien ins Dorf, das ist gut für meinen Käseverkauf. Aber die Steuererhöhung trifft mich direkt – 240 CHF mehr pro Jahr bei meinem Betrieb sind nicht zu vernachlässigen. Was denkst du als Ladenbesitzerin darüber? |  |  |  |  |  |
| L05 | de | 70B · tenant · Mechanikerin in einer kleinen Werkstatt für Landmaschinenreparatur · mood_shift | Die Sorge bleibt, ob die zusätzlichen CHF 144 ausreichen, um die steigenden Mietkosten und Lebenshaltungskosten zu decken, aber ich hoffe, dass die Investition in die Gemeinde langfristig mehr Sicherheit bringt |  |  |  |  |  |
| L06 | de | 70B · municipal_employee · Sachbearbeiterin Finanzen im Gemeindeverwaltung Linden · chat | Herr Steiner, ich weiss, dass die Steuererhöhung für viele Landwirte spürbar ist. Aber denken Sie an die Kinder, die morgen in unsere Gemeinde kommen werden. Ein neues Schulhaus mit Tagesschule und behindertengerechter Turnhalle bedeutet nicht nur bessere Bildung, sondern auch mehr Chancengleichheit und sozialen Zusammenhalt. Das ist eine Investition in die Zukunft von Linden, die uns alle stärkt. |  |  |  |  |  |
| L07 | de | 70B · farmer · Inhaberin eines biologisch geführten Milch- und Ackerbaubetriebs · chat | Herr Weber, ich habe die Zahlen der Vorlage P1 und P3 gründlich studiert. Einerseits verstehe ich die Notwendigkeit, das Schulhaus zu erneuern – es ist eine Investition in die Arbeitskräfte von morgen, die wiederum Betriebe wie den meinen brauchen. Andererseits berechnet die Vorlage für meinen Haushalt etwa 432 CHF mehr Steuern pro Jahr. Können wir nicht einen Weg finden, die Last fairer zu verteilen, ohne die regionale Kaufkraft zu gefährden? Ich habe eine Idee für einen langfristigen Finanzierungsplan, der die Landwirtschaft nicht stranguliert, aber ich fürchte, er wird als Angriff gewertet. |  |  |  |  |  |
| L08 | de | 70B · farmer · Milchkuhhalterin mit Direktvermarktung · mood_shift | Ich versuche, die Fakten nüchtern zu betrachten, bevor ich eine endgültige Meinung bilde. |  |  |  |  |  |
| L09 | de | 70B · farmer · biologisch-dynamischer Landwirt · mood_shift | Die Angst, dass die Gemeinde die Tragfähigkeit unserer Betriebe aus den Augen verliert, verstärkt sich, während die öffentliche Diskussion weiterhin schwach bleibt. |  |  |  |  |  |
| L10 | de | 70B · farmer · Milchkuhhalterin mit Direktvermarktung · chat | Sabine, ich verstehe die Notwendigkeit der Steuererhöhung, aber für meinen Betrieb bedeutet das eine spürbare Mehrbelastung. Können wir im Budget eine Klausel einbauen, die die Unterstützung für lokale Direktvermarkter bei der Finanzierung von Infrastruktur berücksichtigt? Das würde die Attraktivität der Gemeinde für Familien und damit auch für meinen Käse und Joghurt erhöhen. |  |  |  |  |  |
| L11 | de | 70B · farmer · biologisch-dynamischer Landwirt · chat | Walter, ich habe die Vorlage gelesen. Der Steuerfuss steigt um sechs Prozentpunkte. Für einen Betrieb wie den Sonnenrain bedeutet das bei unserem Gewinn eine spürbare Belastung. Wir tragen bereits zur Wertschöpfung bei – warum sollen wir jetzt die Hauptlast tragen, während die Gemeinde ihre Defizite mit unseren Gewinnen deckt? |  |  |  |  |  |
| L12 | de | 70B · farmer · biologisch-dynamischer Landwirt · chat | Ursula, ich muss Ihnen ehrlich sagen: Die geplante Steuererhöhung trifft Betriebe wie meinen hart. Wir tragen bereits zur Wertschöpfung bei und schaffen Arbeitsplätze. Ein zusätzlicher Belastungsfaktor gefährdet die langfristige Stabilität, die wir doch alle wollen. |  |  |  |  |  |
| L13 | de | 70B · tenant · carpenter (Berufslehre in Basel, arbeitet bei einer lokalen Zimmerei) · chat | Thierry, ich habe die Vorlage für den Steuerfuss und den Schulhausneubau gelesen. Ich bin dafür, weil wir damit verhindern, dass die Gemeinde bei den sozialen Leistungen sparen muss. Meine Partnerin und ich sind froh, dass wir bisher durchgekommen sind, aber wenn die Sozialhilfe gekürzt wird, trifft das auch Leute aus unserem Umfeld. Ein neues Schulhaus ist eine Investition in die Zukunft, und die Zimmerei Meier wird sicher Aufträge dafür bekommen. Was denkst du als Ladenbesitzer darüber? |  |  |  |  |  |
| L14 | de | 70B · municipal_employee · Leiter der Abteilung Finanzen und Steuern (Finance and Taxes Division) · chat | Léa, ich habe mir die Zahlen nochmals angesehen. Bei einem Defizit von 1,2 Millionen CHF und einer Steuererhöhung von 6 Prozentpunkten sehe ich das Problem: Wir belasten die Steuerzahler zusätzlich, ohne dass die Effizienz der Ausgaben wirklich verbessert wird. Für deine Boutique bedeutet das weniger Kaufkraft bei den Kunden, und für die Gemeinde riskieren wir, dass die Rückstellungen für Strassen und Sozialhilfe weiter schrumpfen. Wir sollten lieber nach Einsparungen suchen, bevor wir die Steuerfuss erhöhen. |  |  |  |  |  |
| L15 | de | 8B · shopkeeper · Kioskbetreiberin · chat | Herr Stadtplaner, ich verstehe nicht, wie die Gemeinde die Verwendung der 4.8 Millionen CHF für den Schulbau rechtfertigen will, wenn meine Kosten bereits an die Decke gehen. Die Steuererhöhung trifft genau die, die am wenigsten Spielraum haben, um Verluste zu kompensieren. |  |  |  |  |  |
| L16 | de | 8B · tenant · Architekturplaner (freelance) · mood_shift | Ich halte die Lage nüchtern abzuwägen, um eine fundierte Entscheidung zu treffen. |  |  |  |  |  |
| L17 | de | 8B · farmer · Landwirtin (small-scale mixed farm) · chat | Céline, ich verstehe Ihre Sorge um die Lebenshaltungskosten. Der Steuerfuss-Anstieg bringt zwar kurzfristig 240 CHF mehr Steuern, doch der Schulhauskredit schafft langfristig Arbeitsplätze und stärkt unsere lokale Infrastruktur. Die Investition in Bildung und Bau ist der beste Weg, um die Lebensqualität zu erhöhen, ohne die Preise für Grundnahrungsmittel steigen zu lassen. |  |  |  |  |  |
| L18 | de | 8B · tenant · Architekturplaner (freelance) · chat | Céline, ich verstehe Ihre Bedenken bezüglich der zusätzlichen Steuerbelastung, doch die Investition in den Schulhausneubau 2027 stärkt die langfristige Infrastruktur und unterstützt damit auch meine nachhaltigen Erweiterungsprojekte. Die Berechnung zeigt, dass meine Steuerbelastung zwar steigt, aber der Nutzen für die Gemeinde und meine Arbeit überwiegt. |  |  |  |  |  |
| L19 | de | 8B · tenant · Architekturplaner (freelance) · chat | Céline, die Steuererhöhung mag kurzfristig belasten, doch der Schulhausbau 2027 stärkt langfristig unsere Infrastruktur und schafft damit die Grundlage für nachhaltige Erweiterungen wie meine. |  |  |  |  |  |
| L20 | de | 8B · municipal_employee · Stadtplaner im Amt für Raumplanung der Gemeinde Linden · chat | Herr Girard, ich verstehe Ihre Bedenken bezüglich der Steuerbelastung, doch die Daten zeigen klar, dass die Erhöhung des Steuerfusses und der Schulhauskredit langfristig die Lebensqualität sichern und Arbeitsplätze schaffen. Die CHF 4.8 Millionen für den Neubau werden lokale Firmen beschäftigen und die Abhängigkeit von externen Investoren reduzieren. |  |  |  |  |  |
| L21 | fr | 70B · teacher · enseignante de français et d'histoire au Cycle d'orientation de Linden · chat | Petra, j'ai besoin de te parler. J'ai bien lu les comptes 2025 : un déficit de 1,2 million CHF. Mais augmenter le taux d'imposition de 118 % à 124 % pour financer ce projet, c'est 240 CHF de plus par an pour moi. Comment peut-on justifier une ponction fiscale qui pèse sur les locataires comme nous, sans garantie que cet argent reste dans la commune pour nos artisans ? |  |  |  |  |  |
| L22 | fr | 70B · shopkeeper · propriétaire d'une épicerie fine à Linden · mood_shift | Je me sens plus confiante en voyant que l'investissement dans l'école peut attirer une clientèle plus nombreuse et plus aisée, ce qui est bon pour mon chiffre d'affaires à long terme. |  |  |  |  |  |
| L23 | fr | 70B · teacher · enseignant de mathématiques au Cycle d'orientation de Linden · chat | Ursula, j'ai analysé les comptes du budget 2027. Le report du chantier coûterait plus cher à la commune à long terme qu'une hausse temporaire du taux d'imposition. Les chiffres montrent que l'impact annuel moyen par ménage reste raisonnable face à la valeur ajoutée d'une école moderne pour nos enfants. |  |  |  |  |  |
| L24 | fr | 70B · shopkeeper · propriétaire d'une boutique de produits artisanaux suisses · chat | Hans, je ne peux pas accepter cette hausse du taux d'imposition sans une garantie que les bénéfices pour les commerçants compensent la perte de pouvoir d'achat. L'accueil de jour peut attirer plus de monde dans la rue du village, mais si les familles doivent payer 432 CHF de plus par an, elles achèteront moins de produits artisanaux. Ne pensez-vous pas que des subventions ciblées pour les apprentis seraient plus efficaces pour soutenir l'économie locale que cette ponction fiscale ? |  |  |  |  |  |
| L25 | fr | 70B · shopkeeper · propriétaire d'une boutique de produits artisanaux suisses · mood_shift | L'incertitude pèse sur mes prévisions budgétaires : je ne sais pas encore si l'afflux de clients compensera la hausse des charges fiscales. |  |  |  |  |  |
| L26 | fr | 70B · teacher · enseignante de français et d'histoire au Cycle d'orientation de Linden · mood_shift | Mon inquiétude grandit en pensant que cette augmentation du taux d'imposition de 118 % à 124 % va réduire mon pouvoir d'achat et rendre mon budget encore plus fragile, sans garantie que cet argent reste dans la commune |  |  |  |  |  |
| L27 | fr | 70B · teacher · enseignant de mathématiques au cycle d'orientation de Linden · chat | Céline, je sais que tu te demandes comment une hausse d'impôt peut être bénéfique pour ton commerce. Mais imagine que la nouvelle structure d'accueil de jour attire des familles qui resteront plus longtemps dans la commune, et que les nouvelles salles de classe améliorent la réputation de nos écoles. À long terme, cela attire des investissements et stabilise notre pouvoir d'achat. Le budget 2027 prévoit 4,8 millions pour l'école, c'est un investissement qui protège notre avenir économique. |  |  |  |  |  |
| L28 | fr | 70B · shopkeeper · propriétaire d'une quincaillerie familiale à Linden · mood_shift | Je reste préoccupé : d'un côté, l'école attire les familles et stimule la demande pour mes produits ; de l'autre, la hausse d'impôt menace ma capacité à investir et à garder mes prix compétitifs. Sans chiffres fiables sur la capacité de remboursement de la commune, je ne peux pas me décider. |  |  |  |  |  |
| L29 | fr | 70B · teacher · enseignant de mathématiques au Cycle d'orientation de Linden · chat | Ursula, j'ai regardé les comptes provisoires. Le budget 2027 prévoit cette dépense, mais le taux d'imposition passe de 118 à 124 %. Pour un ménage moyen, c'est environ 240 CHF de plus par an. Comment le conseil communal justifie-t-il ce choix face à la pression sur le pouvoir d'achat ? |  |  |  |  |  |
| L30 | fr | 70B · teacher · enseignante de français et d'histoire au Cycle d'orientation de Linden · chat | Léa, je viens de voir l'objet concernant la hausse du taux d'imposition. Avec cette augmentation, je devrais payer environ 240 CHF de plus par an. Pour moi, c'est une charge supplémentaire qui grignote mon budget mensuel, surtout que je vis en location. Tu ne trouves pas que c'est beaucoup pour un projet qui profite surtout aux entreprises de Zurich ? |  |  |  |  |  |
| L31 | fr | 70B · shopkeeper · propriétaire d'une quincaillerie familiale à Linden · chat | Walter, j'ai besoin de ton avis d'artisan. Tu as déjà vu les plans de l'école ? Comment penses-tu que cela va impacter tes commandes de fenêtres et de portes ? Et cette hausse d'impôt, comment la vois-tu pour ton entreprise ? |  |  |  |  |  |
| L32 | fr | 70B · shopkeeper · propriétaire d'une quincaillerie familiale à Linden · chat | Walter, tu as lu les chiffres ? Si le taux d'imposition passe à 124 %, mon tiroir-caisse risque de se vider plus vite que les sacs de ciment que tu commandes pour les nouvelles maisons. Mais si l'école attire des familles, ma quincaillerie vendra plus de fenêtres et de vis. Tu vois le problème ? |  |  |  |  |  |
| L33 | fr | 70B · teacher · enseignant de mathématiques au Cycle d'orientation de Linden · chat | Ursula, ta vision des chiffres et des enfants me rassure. Tu sais que je prépare des graphiques pour montrer que la hausse d'impôt est proportionnelle à l'enrichissement collectif que ces infrastructures apportent. Mais comment convaincre les sceptiques que l'école n'est pas un luxe mais une infrastructure vitale comme les routes ? |  |  |  |  |  |
| L34 | fr | 70B · shopkeeper · propriétaire d'une boutique de produits artisanaux suisses · mood_shift | Je ressens une inquiétude croissante : si le taux d'imposition augmente, mes marges diminuent, et même si la garderie attire plus de clients, je ne sais pas si cela suffira à compenser la charge supplémentaire. La tension entre solidarité communale et survie économique de ma boutique me pèse. |  |  |  |  |  |
| L35 | fr | 8B · tenant · architect · chat | Gemeinde Linden, je suis inquiet quant à l'équilibre entre l'investissement dans l'école et l'augmentation de mon impôt sur le bien immobilier. Les 4,8 millions CHF pour le bâtiment scolaire semblent un investissement nécessaire, mais le surcoût annuel de 240 CHF pour un revenu de 80 000 CHF me complique les projets de rénovation. |  |  |  |  |  |
| L36 | fr | 8B · shopkeeper · proprietor of a boutique retail shop in Linden · chat | Henri, tu enseignes aux enfants qui demain seront nos clients. Ce bâtiment scolaire va attirer des familles, donc plus de clientèle pour nous tous. Le crédit de 4,8 millions CHF stimulera la demande locale. |  |  |  |  |  |
| L37 | fr | 8B · shopkeeper · proprietor of a boutique retail shop in Linden · chat | Henri, je suis indécise sur cette question. Le crédit de 4,8 millions CHF pour l'école stimulera la demande locale et renforcera l'attractivité de Linden, ce qui est bénéfique pour mon entreprise. Mais la hausse du taux d'imposition de 118 % à 124 % alourdit ma charge fiscale et réduit ma marge pour investir dans l'innovation et le service client. |  |  |  |  |  |
| L38 | fr | 8B · teacher · primary school teacher · chat | Céline, cette hausse de 6 points représente 240 CHF de plus par an pour un ménage modeste comme le nôtre, alors que les justifications budgétaires restent floues. Comment justifier une telle charge sans transparence claire? |  |  |  |  |  |
| L39 | fr | 8B · tenant · architect · chat | Gemeinde Linden, je comprends votre vision d'autonomie économique, mais je reste sceptique sur l'efficacité de l'usage des fonds publics. Le crédit de 4,8 millions CHF pour l'école est un investissement à long terme, mais l'augmentation du taux d'imposition me pèse sur mes projets de rénovation. |  |  |  |  |  |
| L40 | fr | 8B · teacher · primary school teacher · mood_shift | L'incertitude sur l'usage des fonds et la charge fiscale supplémentaire me rendent particulièrement inquiet pour l'avenir financier de ma famille. |  |  |  |  |  |

## D. Free comments

Anything systematically wrong (a word the model always uses, a tone that is off, missing Swiss terms):
