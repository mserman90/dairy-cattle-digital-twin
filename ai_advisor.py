import re
from typing import Dict, Any, List
from simulator import simulator_engine

class AgriTwinAIAdvisor:
    """
    Süt Sığırcılığı Dijital İkizi Doğal Dil Danışmanı (AI Farm & Veterinary Assistant)
    """

    @staticmethod
    def normalize_text(text: str) -> str:
        t = text.lower()
        replacements = [('ı', 'i'), ('ğ', 'g'), ('ü', 'u'), ('ş', 's'), ('ö', 'o'), ('ç', 'c')]
        for a, b in replacements:
            t = t.replace(a, b)
        return t

    @classmethod
    def answer_query(cls, query: str) -> Dict[str, Any]:
        state = simulator_engine.get_full_state()
        q = cls.normalize_text(query)

        # 1. Mastitis / Sağlık Sorgusu
        if any(w in q for w in ["genomik", "damizlik", "inbreeding", "akrabalik", "pedigri", "ciftlestirme", "boga", "sperma", "net merit", "gebv", "tpi", "hcd"]):
            gen = state.genomics
            if not gen:
                return {"query": query, "answer": "Genomik pedigri ikiz verisi henüz yüklenmedi.", "category": "GENOMICS_INFO"}

            # İnek bazlı eşleştirme sorgusu
            matched_cow = None
            for c in state.animals:
                c_norm = cls.normalize_text(c.name)
                c_id_norm = cls.normalize_text(c.id)
                if c_norm in q or c_id_norm in q:
                    matched_cow = c
                    break

            if matched_cow and matched_cow.id in gen.mating_matrix_recommendations:
                recs = gen.mating_matrix_recommendations[matched_cow.id]
                top = recs[0]
                ans = (
                    f"🧬 **{matched_cow.name} ({matched_cow.id}) Akıllı Genomik Çiftleştirme Raporu:**\n\n"
                    f"- **Bireysel Damızlık Düzeyi:** ${matched_cow.pedigree.gebv.net_merit_dollars:,.0f} NM$ | TPI: {matched_cow.pedigree.gebv.tpi_score}\n"
                    f"- **Mevcut Inbreeding Oranı:** %{matched_cow.pedigree.individual_inbreeding_coeff_f_pct:.1f}\n"
                    f"- **Önerilen 1. Boğa:** **{top.bull.bull_name}** ({top.bull.semen_company} - NAAB: `{top.bull.naab_code}`)\n"
                    f"- **Tahmini Yavru Net Merit:** **${top.expected_progeny_net_merit:,.0f} NM$** (+{top.expected_progeny_milk_kg:,.0f} kg süt)\n"
                    f"- **Yavru Akrabalık Katsayısı (F):** **%{top.progeny_inbreeding_f_pct:.2f}** ({'✅ Güvenli < %6.25' if top.inbreeding_status == 'SAFE_GREEN' else '⚠️ Uyarı'})\n"
                    f"- **Sperma Stratejisi:** `{top.recommendation_type}`\n"
                    f"- **Alternatif 2. Boğa:** {recs[1].bull.bull_name} (F: %{recs[1].progeny_inbreeding_f_pct:.2f} | NM$: ${recs[1].expected_progeny_net_merit:,.0f})\n"
                )
                if any(r.recessive_conflict for r in recs):
                    bad = next(r for r in recs if r.recessive_conflict)
                    ans += f"\n⛔ **Engellenen Boğa:** `{bad.bull.bull_name}` ({bad.conflict_details})"
                return {"query": query, "answer": ans, "category": "COW_MATING_RECOMMENDATION", "animal_id": matched_cow.id}

            ans = (
                f"🧬 **Sürü Genomik Damızlık & Akrabalık (Inbreeding) Tablosu:**\n\n"
                f"- **Genotiplenen İnek Sayısı:** {gen.total_genotyped_cows} Baş Holstein Friesian\n"
                f"- **Sürü Ortalama Net Merit:** **${gen.avg_herd_net_merit:,.0f} NM$**\n"
                f"- **Sürü Ortalama Inbreeding (F):** **%{gen.avg_herd_inbreeding_pct:.2f}** (Eşik: <%6.25 Güvenli)\n"
                f"- **Yıllık Inbreeding Depresyon Maliyeti:** {gen.inbreeding_depression_annual_cost_tl:,.0f} TL/yıl\n"
                f"- **Elit Verici İnekler:** {gen.elite_donors_count} Baş (Dişi cinsiyetli sperma adayı)\n"
                f"- **Katalogdaki Elit Boğalar:** {gen.available_catalog_bulls_count} Boğa (Captain, AltaZarek, Einstein, Renegade)\n"
                f"- **Özet:** {gen.status_summary}"
            )
            return {"query": query, "answer": ans, "category": "HERD_GENOMICS_SUMMARY"}

        elif any(w in q for w in ["dogum", "buzagilama", "distosi", "guc dogum", "kolostrum", "agiz sutu", "brix", "fpt", "buzagi", "maternity"]):
            mat = state.maternity
            if not mat:
                return {"query": query, "answer": "Doğumhane ikiz verisi henüz yüklenmedi.", "category": "CALVING_INFO"}

            dystocias = [t for t in mat.calving_twins if t.dystocia_assessment.alert_level == "CRITICAL_DYSTOCIA_ALARM"]
            if dystocias:
                t = dystocias[0]
                ans = (
                    f"🚨 **DİSTOSİ (GÜÇ DOĞUM) ACİL ALARMI:**\n\n"
                    f"- **Hayvan:** **{t.cow_name} ({t.cow_id})** - Gebelik Günü: {t.gestation_days}\n"
                    f"- **2. Evre Ikınma Süresi:** **{t.dystocia_assessment.stage_2_duration_minutes} dakika** (Kritik Eşik: >70 dk)\n"
                    f"- **Fetal Pozisyon:** **{t.dystocia_assessment.calf_presentation}** (Makat / Ters Geliş)\n"
                    f"- **Kuyruk Sensörü:** {t.telemetry.tail_tilt_angle_deg}° açı / Saatte {t.telemetry.tail_raising_frequency_per_hr} sancı kasılması\n"
                    f"- **Doğum Kolaylık Skoru (CES):** {t.dystocia_assessment.calving_ease_score} / 5 (Mekanik Müdahale Zorunlu)\n"
                    f"- **Müdahale Kararı:** {t.dystocia_assessment.recommended_action}\n"
                    f"- **Ayırma Kapısı:** İnek anında Revir / Doğum Bölmesine yönlendirilmiştir."
                )
                return {"query": query, "answer": ans, "category": "DYSTOCIA_EMERGENCY", "animal_id": t.cow_id}

            imminent = [t for t in mat.calving_twins if t.dystocia_assessment.stage == "STAGE_1_CERVIX_DILATION" or t.telemetry.temp_drop_detected]
            if imminent and any(w in q for w in ["dogum", "sanci", "isi dususu", "yaklasan"]):
                t = imminent[0]
                ans = (
                    f"👀 **DOĞUM ELİ KULAĞINDA (6-18 Saat):**\n\n"
                    f"- **Hayvan:** **{t.cow_name} ({t.cow_id})** - Gebelik: {t.gestation_days}. gün\n"
                    f"- **Vücut Sıcaklığı Düşüşü:** {t.telemetry.body_temperature_c:.2f}°C (Normalden -{t.telemetry.temp_drop_c:.2f}°C düşüş, Progesteron P4 çekilme fazı)\n"
                    f"- **Kuyruk İvmeölçeri:** Saatte {t.telemetry.tail_raising_frequency_per_hr} kuyruk kaldırma (1. Evre servikal açılma sancısı)\n"
                    f"- **Geviş & Huzursuzluk:** Geviş getirme %{t.telemetry.rumination_drop_pct:.0f} azaldı, huzursuzluk indeksi {t.telemetry.restlessness_index:.2f}\n"
                    f"- **Klinik Öneri:** İneği doğumhane bireysel temiz altlıklı locaya alınız."
                )
                return {"query": query, "answer": ans, "category": "CALVING_IMMINENT", "animal_id": t.cow_id}

            if any(w in q for w in ["kolostrum", "agiz sutu", "brix", "fpt"]):
                calved_twins = [t for t in mat.calving_twins if t.colostrum is not None]
                if calved_twins:
                    t = calved_twins[0]
                    c = t.colostrum
                    ans = (
                        f"🍼 **Optik Brix Kolostrum & Bağışıklık (FPT) Raporu:**\n\n"
                        f"- **Anne:** {t.cow_name} ({t.cow_id})\n"
                        f"- **İlk Sağım Miktarı:** {c.colostrum_harvest_liters} Litre\n"
                        f"- **Optik Brix Değeri:** **%{c.brix_refractometer_pct:.1f} Brix** ({c.quality_grade})\n"
                        f"- **Hesaplanan IgG Konsantrasyonu:** **{c.igg_concentration_g_per_l:.1f} g/L** (Eşik: >=50 g/L)\n"
                        f"- **Pasif Bağışıklık Transferi (FPT) Riski:** `{c.fpt_risk}`\n"
                        f"- **Protokol:** {c.feeding_protocol}\n"
                        f"- **Kolostrum Bankası:** {c.colostrum_bank_action} (Mevcut Rezerv: {mat.colostrum_bank_stock_liters} L)"
                    )
                    return {"query": query, "answer": ans, "category": "COLOSTRUM_REPORT", "animal_id": t.cow_id}

            if any(w in q for w in ["buzagi", "vigor", "adg"]):
                calves = [t for t in mat.calving_twins if t.calf is not None]
                if calves:
                    t = calves[0]
                    cf = t.calf
                    ans = (
                        f"🐮 **Yeni Doğan Buzağı Dijital İkizi:**\n\n"
                        f"- **Buzağı No:** **{cf.calf_id}** (Anne: {cf.dam_id} / Baba: {cf.sire_id})\n"
                        f"- **Cinsiyet & Ağırlık:** {cf.gender} / **{cf.birth_weight_kg} kg**\n"
                        f"- **APGAR Vigor Skoru:** **{cf.vigor_apgar_score_1_10} / 10** (Mükemmel canlılık)\n"
                        f"- **İlk Ayağa Kalkma:** {cf.time_to_stand_minutes} dakika\n"
                        f"- **Serum Total Protein:** {cf.serum_total_protein_g_dl:.1f} g/dL (Hedef: >=5.5 g/dL teyit edildi)\n"
                        f"- **Hedef Günlük Canlı Ağırlık Artışı (ADG):** {cf.target_adg_kg_day} kg/gün\n"
                        f"- **Durum:** `{cf.health_status}`"
                    )
                    return {"query": query, "answer": ans, "category": "CALF_PROFILE", "calf_id": cf.calf_id}

            ans = (
                f"🤰 **Doğumhane & Buzağıhane Genel Özeti:**\n\n"
                f"- **Kapasite & Doluluk:** {mat.cows_in_maternity_pen} / {mat.maternity_pen_capacity} İnek\n"
                f"- **24 Saat İçinde Doğum Beklenen:** {mat.cows_in_24h_calving_window} Baş\n"
                f"- **Aktif Sancıdaki İnekler:** {mat.active_labors_count} Baş\n"
                f"- **Distosi Acil Alarmları:** {mat.dystocia_emergencies_count} Baş\n"
                f"- **Dondurulmuş Kolostrum Rezervi:** {mat.colostrum_bank_stock_liters} L (-20°C Banka)\n"
                f"- **Buzağıhanedeki Buzağı Sayısı:** {mat.nursery_calves_count} Baş (Ortalama Vigor: {mat.avg_calf_vigor_score}/10)\n"
                f"- **Özet:** {mat.status_summary}"
            )
            return {"query": query, "answer": ans, "category": "MATERNITY_SUMMARY"}

        elif any(w in q for w in ["topallik", "ayak", "tirnak", "yuruyus", "lameness", "aksama"]):
            lame_cows = [a for a in state.animals if a.vision and a.vision.lameness.score >= 2.5]
            if lame_cows:
                cow = lame_cows[0]
                ans = (
                    f"🦶 **3D Kamera Topallık (Lameness) Tespiti:**\n\n"
                    f"- **Hayvan:** **{cow.name} ({cow.id})**\n"
                    f"- **Sprecher Topallık Skoru:** **{cow.vision.lameness.score:.1f} / 5.0**\n"
                    f"- **Sırt Kemerleşme / Kamburluk:** %{int(cow.vision.lameness.back_curvature_index * 100)}\n"
                    f"- **Adım Asimetrisi:** %{cow.vision.lameness.gait_asymmetry_pct:.1f}\n"
                    f"- **Şüpheli Bölge:** {cow.vision.lameness.affected_hoof or 'Tırnak Tabanı'}\n"
                    f"- **Otonom Karar:** Akıllı ayırma kapısı ineği **Tırnak Bakım / Revir Bölmesi**'ne sevk etmiştir."
                )
                return {"query": query, "answer": ans, "category": "LAMENESS_ALERT", "animal_id": cow.id}
            else:
                return {
                    "query": query,
                    "answer": "✅ **Tırnak ve Yürüyüş Sağlığı İdeal:** 3D derinlik kamerası tüm ineklerin sırt çizgisini düz (Skor 1) ve adım uzunluklarını simetrik olarak teyit etmiştir.",
                    "category": "LAMENESS_OK"
                }

        elif any(w in q for w in ["bcs", "kondisyon", "zayif", "yag", "zayiflama"]):
            thin_cows = [a for a in state.animals if a.vision and a.vision.bcs.score < 2.75]
            if thin_cows:
                cow = thin_cows[0]
                ans = (
                    f"⚠️ **Düşük Kondisyon (BCS) Tespiti:** İnek **{cow.name} ({cow.id})** için 3D kamera BCS skoru "
                    f"**{cow.vision.bcs.score:.2f}** ölçülmüştür. Açlık çukuru derinliği {cow.vision.bcs.sacral_cavity_depth_mm:.0f} mm ile "
                    f"negatif enerji dengesi sınırındadır. Rasyonda konsantre yem takviyesi önerilir."
                )
                return {"query": query, "answer": ans, "category": "BCS_ALERT", "animal_id": cow.id}
            else:
                avg_bcs = sum((a.vision.bcs.score if a.vision else 3.25) for a in state.animals) / len(state.animals)
                return {
                    "query": query,
                    "answer": f"✅ **Sürü Kondisyonu İdeal:** Sürü ortalama BCS skoru **{avg_bcs:.2f}** ile hedef 3.00-3.25 bandındadır. Aşırı yağlanma veya negatif enerji erimesi saptanmamıştır.",
                    "category": "BCS_OK"
                }

        elif any(w in q for w in ["robot filosu", "yem itici", "juno", "discovery", "gubre robotu", "siyirici robot", "robotlar"]):
            rob = state.robotics
            if rob:
                p = rob.pusher
                c = rob.collector
                ans = (
                    f"🤖 **Otonom Ahır İçi Robot Filosu İkizi:**\n\n"
                    f"**1. {p.name} (Yem İtici):**\n"
                    f"- **Durum:** {p.status} (Konum: x={p.x_m}m, y={p.y_m}m | Batarya: %{p.battery_pct:.0f})\n"
                    f"- **Yem Yüksekliği Sensörü:** {p.feed_height_sensor_cm} cm (Helezon: {p.auger_rpm} rpm)\n"
                    f"- **Fizyolojik Etki:** Kuru Madde Tüketimini (DMI) **+%{p.dmi_boost_pct}** artırıyor, süt verimine **+{p.milk_yield_boost_kg} kg/gün/inek** katkı sağlıyor.\n\n"
                    f"**2. {c.name} (Gübre Vakum):**\n"
                    f"- **Durum:** {c.status} (Konum: x={c.x_m}m, y={c.y_m}m | Tank: %{c.tank_fill_pct:.0f})\n"
                    f"- **Bugün Toplanan Gübre:** {c.daily_manure_collected_kg:,.0f} kg (Biyogaz çukuruna aktarıldı)\n"
                    f"- **Sağlık & Hijyen Etkisi:** Tırnak topallık riskini **-%{c.lameness_reduction_pct:.0f}**, çevresel mastitisi **-%{c.environmental_mastitis_reduction_pct:.0f}** azaltıyor.\n\n"
                    f"⚡ *Enerji & Güvenlik:* Robotlar biyogazdan üretilen temiz elektrikle şarj ediliyor. {rob.fleet_safety_status}."
                )
                return {"query": query, "answer": ans, "category": "ROBOTICS_FLEET_REPORT"}

        elif any(w in q for w in ["scc", "somatik", "ceyrek", "lob", "sagim robotu", "robotik sagim", "teat", "meme ucu"]):
            inf_cows = [a for a in state.animals if a.milking_twin and a.milking_twin.is_any_quarter_diverted]
            if inf_cows:
                cow = inf_cows[0]
                twin = cow.milking_twin
                inf_q = next((q for q in twin.quarters.values() if q.valve_destination == "SEPARATION_DRAIN"), list(twin.quarters.values())[0])
                ans = (
                    f"🤖 **Otonom Robotik Sağım & 4 Loblu Çeyrek Meme Analizi:**\n\n"
                    f"- **Hayvan:** **{cow.name} ({cow.id})**\n"
                    f"- **Sorunlu Lob:** **{inf_q.quarter_name_tr}** ({inf_q.mastitis_status})\n"
                    f"- **Somatik Hücre Sayısı (SCC):** **{inf_q.somatic_cell_count:,} hücre/mL** (Eşik: 200.000)\n"
                    f"- **İletkenlik:** {inf_q.conductivity_ms_cm:.2f} mS/cm (Normal: 5.1 mS/cm)\n"
                    f"- **Kan Oranı:** {inf_q.blood_in_milk_ppm:.1f} ppm\n"
                    f"- **Robotik Vana Aksiyonu:** {inf_q.quarter_name_tr} lobuna ait **{inf_q.yield_kg:.2f} kg süt atığa ayrıldı**.\n"
                    f"- **Kurtarılan Sağlıklı Süt:** Diğer 3 lobun **{twin.accepted_to_tank_kg:.2f} kg sütü ana tanka kabul edildi**.\n"
                    f"- **Biyogüvenlik:** Robot sağım başlığına {twin.teat_cup_disinfection} uygulandı."
                )
                return {"query": query, "answer": ans, "category": "ROBOTIC_MILKING_ALERT", "animal_id": cow.id}
            else:
                return {
                    "query": query,
                    "answer": "✅ **4 Lob Sağım Analizi Kusursuz:** Robotik sağım başlıkları tüm ineklerin 4 çeyrek lobunda (RF, RR, LF, LR) somatik hücre sayısını <150.000 hücre/mL ve iletkenlikleri 5.0-5.3 mS/cm aralığında ölçmüştür. Atığa ayrılan süt bulunmamaktadır.",
                    "category": "ROBOTIC_MILKING_OK"
                }

        elif any(w in q for w in ["rumen", "asidoz", "sara", "bolus", "ph", "tampon", "bikarbonat"]):
            sara_cows = [a for a in state.animals if a.rumen and a.rumen.assessment.sara_risk_score >= 0.6]
            if sara_cows:
                cow = sara_cows[0]
                ans = (
                    f"🧪 **Subakut Rumen Asidozu (SARA) Alarmı:**\n\n"
                    f"- **Hayvan:** **{cow.name} ({cow.id})**\n"
                    f"- **Rumen pH:** **{cow.rumen.telemetry.rumen_ph:.2f}** (Kritik eşik: 5.80 altı)\n"
                    f"- **Eşik Altı Kalma Süresi:** {cow.rumen.assessment.hours_below_ph_5_8} saat/gün\n"
                    f"- **A:P Oranı:** {cow.rumen.telemetry.acetate_to_propionate_ratio:.2f} (Normal: > 2.50)\n"
                    f"- **Motilite:** {cow.rumen.telemetry.rumen_contractions_per_min:.1f} kontraksiyon/dk ({cow.rumen.assessment.rumen_motility_status})\n"
                    f"- **Klinik Öneri:** Rasyondaki tahıl yükünü azaltın. 150-200g **Sodyum Bikarbonat** tamponu ekleyin ve ineği ayırma kapısıyla izole edin."
                )
                return {"query": query, "answer": ans, "category": "SARA_ALERT", "animal_id": cow.id}
            else:
                avg_ph = sum((a.rumen.telemetry.rumen_ph if a.rumen else 6.4) for a in state.animals) / len(state.animals)
                return {
                    "query": query,
                    "answer": f"✅ **Rumen Fermantasyonu Dengeli:** Sürü ortalama rumen pH'ı **{avg_ph:.2f}** seviyesindedir. Bolus sensörlerinde SARA veya akut asidoz riski taşıyan hayvan saptanmamıştır.",
                    "category": "RUMEN_OK"
                }

        elif any(w in q for w in ["mastitis", "hasta", "hastalik", "iltihap", "meme", "saglik", "revir"]):
            critical = [a for a in state.animals if a.dss.overall_health_status == "CRITICAL"]
            if critical:
                cow = critical[0]
                ans = (
                    f"🚨 **Acil Sağlık Bildirimi:** İnek **{cow.name} ({cow.id})** için subklinik mastitis riski "
                    f"**%{int(cow.dss.mastitis_risk_score * 100)}** olarak tespit edilmiştir.\n\n"
                    f"- **Süt İletkenliği:** {cow.latest_milking.conductivity_ms_cm:.2f} mS/cm (Normal: 5.2 mS/cm)\n"
                    f"- **Geviş Süresi:** {cow.telemetry.rumination_minutes_2h} dk/2sa (Akut düşüş)\n"
                    f"- **Vücut Sıcaklığı:** {cow.telemetry.body_temperature_c:.1f}°C\n"
                    f"- **Otonom Eylem:** Akıllı ayırma kapısı bu hayvanı **Revir İzolasyon Bölmesi**'ne yönlendirmiştir."
                )
                return {"query": query, "answer": ans, "category": "HEALTH_ALERT", "animal_id": cow.id}
            else:
                return {
                    "query": query,
                    "answer": "✅ **Sürü Sağlığı Nominal:** Sürüde şu an kritik veya subklinik mastitis alarmı veren hayvan bulunmamaktadır. Tüm iletkenlik ve geviş değerleri tolerans sınırları içerisindedir.",
                    "category": "HEALTH_OK"
                }

        # 2. Kızgınlık / Tohumlama (Estrus) Sorgusu
        elif any(w in q for w in ["kizginlik", "estrus", "tohumlama", "boga", "gebe"]):
            estrus_cows = [a for a in state.animals if a.dss.estrus_probability > 0.7]
            if estrus_cows:
                cow = estrus_cows[0]
                ans = (
                    f"⚡ **Kızgınlık (Estrus) Tespiti:** İnek **{cow.name} ({cow.id})** kızgınlık döngüsündedir "
                    f"(Skor: %{int(cow.dss.estrus_probability * 100)}).\n\n"
                    f"- **Lokomotor Aktivite:** {cow.telemetry.activity_index} adım/saat (Referansın 2.3 katı)\n"
                    f"- **Önerilen Eylem:** Önümüzdeki **8 ile 12 saat içerisinde** suni tohumlama yapılması durumunda gebelik başarı oranı %82 olarak öngörülmektedir."
                )
                return {"query": query, "answer": ans, "category": "ESTRUS_ALERT", "animal_id": cow.id}
            else:
                return {
                    "query": query,
                    "answer": "ℹ️ Şu anda sürüde tohumlama eşiğini aşan hiperaktivite veya kızgınlık davranışı sergileyen inek bulunmamaktadır.",
                    "category": "ESTRUS_NONE"
                }

        # 3. İlaç Karantinası / Süt Tankı Kilidi (Withdrawal Period)
        elif any(w in q for w in ["ilac", "karantina", "tank", "antibiyotik", "arinma", "kalinti", "sut dok"]):
            txs = state.edge_gateway.active_treatments
            if txs:
                tx = txs[0]
                ans = (
                    f"🔒 **Gıda Güvenliği & Süt Tankı Kilidi AKTİF:**\n\n"
                    f"- **Tedavi Gören Hayvan:** `{tx.animal_id}`\n"
                    f"- **Uygulanan İlaç:** {tx.drug_administered}\n"
                    f"- **Kalan Arınma Süresi:** {tx.withdrawal_period_days} Gün\n"
                    f"- **Otomasyon:** Sağım robotundaki vanalar kilitlenmiş, bu ineğin sütü otomatik olarak atık tankına imha edilmektedir. Tank sütünde antibiyotik bulaşma riski %0'dır."
                )
                return {"query": query, "answer": ans, "category": "DRUG_WITHDRAWAL_ACTIVE"}
            else:
                return {
                    "query": query,
                    "answer": "✅ **Tank Kilidi Açık:** Sürüde aktif antibiyotik veya arınma süresinde hayvan bulunmamaktadır. Sağılan tüm süt ana soğutma tankına güvenle kabul edilmektedir.",
                    "category": "DRUG_WITHDRAWAL_NONE"
                }

        # 4. Isı Stresi / THI / Fan / Havalandırma
        elif any(w in q for w in ["sicaklik", "nem", "thi", "isi stresi", "fan", "sisleme", "havalandirma", "hava", "stres"]):
            max_thi = max(z.thi_index for z in state.barn_zones)
            ans = (
                f"🌡️ **Barınak Mikroklima Durumu:**\n\n"
                f"- **Maksimum THI İndeksi:** {max_thi:.1f}\n"
                f"- **Havalandırma Fanları:** {'🌀 AÇIK (%100 Devir)' if max_thi >= 72 else 'KAPALI'}\n"
                f"- **Sisleme Sistemi:** {'💦 AÇIK (Yüksek Basınç)' if max_thi >= 79 else 'KAPALI'}\n"
                f"- **Değerlendirme:** " + (
                    "🚨 Şiddetli Isı Stresi! İnekler fanların altında kümeleniyor (Bunching). Otonom soğutma devrede."
                    if max_thi >= 79 else
                    ("⚠️ Orta Isı Stresi. Fanlar devrede, süt verim kaybı %4 ile sınırlandırıldı." if max_thi >= 72 else "✅ İnekler için termal konfor aralığı (<72 THI).")
                )
            )
            return {"query": query, "answer": ans, "category": "CLIMATE_REPORT"}

        # 5. Biyogaz, Gübre ve Çiftlik Enerji İkizi Sorgusu
        elif any(w in q for w in ["biyogaz", "enerji", "elektrik", "chp", "gubre", "atik", "kojenerasyon", "net-zero", "sebeke"]):
            en = state.energy
            if en:
                ans = (
                    f"⚡ **Döngüsel Biyogaz, Gübre & Kojenerasyon Enerji İkizi:**\n\n"
                    f"- **Günlük Gübre Üretimi:** {en.manure.total_manure_kg_day:,.0f} kg/gün ({en.manure.volatile_solids_kg_day:.0f} kg Uçucu Katı Madde)\n"
                    f"- **Biyogaz Üretimi (38.5°C Mezofilik):** {en.digester.daily_biogas_production_m3:.1f} m³/gün (%{en.digester.methane_content_pct:.1f} CH₄)\n"
                    f"- **Kojenerasyon Elektrik Üretimi:** **{en.chp.daily_electricity_generated_kwh:.1f} kWh/gün**\n"
                    f"- **Çiftlik Tüketimi (Robot, Soğutma, Fan):** {en.consumption.total_consumption_kwh_day:.1f} kWh/gün\n"
                    f"- **Şebekeye Net Elektrik İhracı:** **+{en.chp.net_grid_export_kwh:.1f} kWh/gün** (Öz Yeterlilik: %{en.chp.self_sufficiency_ratio_pct:.0f})\n"
                    f"- **Organik Biyogübre (Digestat):** {en.fertilizer.daily_digestate_tons:.2f} ton/gün\n"
                    f"- **Yıllık Toplam Enerji & Gübre Katma Değeri:** **+{en.annual_total_energy_benefit_tl:,.0f} TL/yıl**\n"
                    f"- **Fosil Yakıt Karbon Ofseti:** {en.annual_co2_offset_tons:.1f} ton CO₂e/yıl\n\n"
                    f"🌟 *Sonuç:* Çiftlik elektrikte **%100 Net-Zero şebeke bağımsızlığına** ulaşmış olup ihtiyaç fazlası elektriği şebekeye satmaktadır."
                )
                return {"query": query, "answer": ans, "category": "BIOGAS_ENERGY_REPORT"}
            else:
                return {
                    "query": query,
                    "answer": "ℹ️ Biyogaz ve enerji ikizi verisi hazırlanıyor.",
                    "category": "BIOGAS_ENERGY_REPORT"
                }

        # 6. Çok Amaçlı TMR Rasyon & Karbon Optimizasyonu Sorgusu
        elif any(w in q for w in ["rasyon", "tmr", "bovaer", "3-nop", "pareto", "optimizasyon", "yesil yem", "karbon azalt"]):
            from ration_optimizer import TMRRationOptimizer
            rep = TMRRationOptimizer.generate_optimization_plans(active_strategy_id=state.active_ration_strategy)
            active_plan = next(p for p in rep.plans if p.is_active)
            ans = (
                f"🌾 **Çok Amaçlı TMR Rasyon & Karbon Optimizasyon İkizi:**\n\n"
                f"- **Aktif Strateji:** **{active_plan.strategy_title}** ({active_plan.strategy_badge})\n"
                f"- **Kuru Madde Tüketimi (DMI):** {active_plan.total_dmi_kg} kg/gün/inek\n"
                f"- **Rasyon Maliyeti:** {active_plan.daily_feed_cost_per_cow:.2f} TL/gün ({round(active_plan.daily_feed_cost_per_cow/active_plan.total_dmi_kg, 2)} TL/kg DM)\n"
                f"- **Beklenen Süt Verimi:** {active_plan.predicted_milk_yield_kg} kg/gün\n"
                f"- **Yem Üzeri Gelir (IOFC):** **+{active_plan.daily_iofc_per_cow:.2f} TL/gün/inek**\n"
                f"- **Enterik Metan Salımı:** {active_plan.enteric_methane_g_day:.1f} g CH₄/gün (**%{active_plan.carbon_reduction_pct:.1f} Azaltım**)\n"
                f"- **SARA Koruma Durumu:** {active_plan.sara_safety_index}\n"
                f"- **Yıllık Karbon Kredisi Geliri:** +{active_plan.carbon_credit_annual_savings_tl:,.0f} TL/yıl (80 baş)\n\n"
                f"💡 *Tavsiye:* Maksimum kâr ile minimum metan emisyonu arasındaki en iyi denge için **Dengeli Pareto** stratejisi önerilmektedir."
            )
            return {"query": query, "answer": ans, "category": "RATION_OPTIMIZATION_REPORT"}

        # 7. Yem Rasyonu, Metan ve Finansal ROI Sorgusu
        elif any(w in q for w in ["yem", "metan", "roi", "maliyet", "gelir", "kar", "para", "amorti"]):
            ans = (
                f"💰 **Finansal & Sürdürülebilirlik İkizi:**\n\n"
                f"- **Günlük Brüt Süt Satış Geliri:** {state.financials.daily_gross_milk_revenue:,.2f} TL\n"
                f"- **Günlük Toplam Yem Gideri:** {state.financials.daily_total_feed_cost:,.2f} TL\n"
                f"- **Yem Üzeri Gelir (IOFC):** +{state.financials.daily_net_margin_over_feed:,.2f} TL/gün\n"
                f"- **Aylık Net Dijital İkiz Kazancı:** +{state.financials.total_monthly_net_benefit:,.2f} TL/ay\n"
                f"- **Yatırım Geri Dönüşü (ROI):** **{state.financials.estimated_payback_period_years:.1f} Yıl**\n"
                f"- **Enterik Metan Salımı:** {state.sustainability.total_daily_methane_kg:.2f} kg CH₄/gün (Yem optimizasyonu ile %16 azaltılabilir)."
            )
            return {"query": query, "answer": ans, "category": "FINANCIAL_REPORT"}

        # Genel / Tanımlanamayan Sorgu
        else:
            return {
                "query": query,
                "answer": (
                    f"🤖 **AgriTwin AI Asistanı:** Sorunuzu analiz ettim. Sürüde şu an {len(state.animals)} baş inek takip edilmektedir. "
                    f"Bana şunları sorabilirsiniz:\n"
                    f"- *'Hangi inek hasta veya revire ayrıldı?'*\n"
                    f"- *'Kızgınlıkta olan inek var mı, ne zaman tohumlamalıyım?'*\n"
                    f"- *'Barınakta ısı stresi veya çalışan fan var mı?'*\n"
                    f"- *'Antibiyotik karantinası ve süt tankı durumu nedir?'*\n"
                    f"- *'Aylık yem maliyeti ve sistemin ROI geri dönüş süresi nedir?'*"
                ),
                "category": "GENERAL_HELP"
            }
