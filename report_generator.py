from datetime import datetime
from typing import Dict, Any
from simulator import simulator_engine

class FarmAuditReportGenerator:
    """
    Veteriner Hekim & Çiftlik Yöneticisi için Günlük Dijital İkiz Denetim Raporu
    """

    @staticmethod
    def generate_daily_audit_markdown() -> str:
        state = simulator_engine.get_full_state()
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        healthy_count = sum(1 for a in state.animals if a.dss.overall_health_status == "HEALTHY")
        warning_count = sum(1 for a in state.animals if a.dss.overall_health_status == "WARNING")
        critical_count = sum(1 for a in state.animals if a.dss.overall_health_status == "CRITICAL")

        lines = [
            f"# 📋 AGRITWIN GÜNLÜK DİJİTAL İKİZ VE VETERİNER DENETİM RAPORU",
            f"**Rapor Tarihi:** {now_str} | **Çiftlik:** {state.farm_name}",
            f"**Sistem Modu:** {state.edge_gateway.connection_mode} | **Simülasyon Adımı:** #{state.simulation_tick}",
            "",
            "---",
            "## 1. 🩺 Sürü Sağlığı ve Erken Uyarı Özeti",
            f"- **Toplam Sürü Varlığı:** {len(state.animals)} Baş Holstein Friesian",
            f"- **Genel Sağlık Durumu:** {healthy_count} Sağlıklı | {warning_count} Takipte | {critical_count} Acil/Revir",
            f"- **Otomatik Ayırma Kapısı Durumu:** `{state.sorting_gate.status}` (Son Sevk: {state.sorting_gate.last_diverted_animal_id or 'Yok'})",
            "",
            "| Küpe No | İsim | DIM | İletkenlik | Geviş (2sa) | Vücut Isısı | Mastitis Riski | XAI Önerisi |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for a in state.animals:
            status_emoji = "✅" if a.dss.overall_health_status == "HEALTHY" else ("⚠️" if a.dss.overall_health_status == "WARNING" else "🚨")
            lines.append(
                f"| `{a.id}` | {a.name} | {a.days_in_milk}g | {a.latest_milking.conductivity_ms_cm:.2f} mS/cm | {a.telemetry.rumination_minutes_2h} dk | {a.telemetry.body_temperature_c:.1f}°C | %{int(a.dss.mastitis_risk_score * 100)} {status_emoji} | {a.dss.recommended_action} |"
            )

        lines.extend([
            "",
            "---",
            "## 2. 💊 Veteriner Tedavi & İlaç Arınma Takibi (Withdrawal Management)",
        ])

        if state.edge_gateway.active_treatments:
            for tx in state.edge_gateway.active_treatments:
                lines.append(f"- 🚨 **Karantina:** Hayvan `{tx.animal_id}` ({tx.diagnosis}) - **İlaç:** {tx.drug_administered} | **Kalan Arınma:** {tx.withdrawal_period_days} Gün")
                lines.append(f"  - *Otomasyon Koruması:* Sağım robotu ana tank kilidi `AKTİF`. Süt atık tankına imha ediliyor.")
        else:
            lines.append("- ✅ *Aktif antibiyotik karantinasında hayvan bulunmamaktadır. Tüm süt ana soğutma tankına kabul edilmektedir.*")

        lines.extend([
            "",
            "---",
            "## 3. 🤰 Doğumhane, Distosi Erken Uyarı & Kolostrum / Buzağı İkizi",
        ])

        if state.maternity:
            m = state.maternity
            lines.extend([
                f"- **Doğumhane Durumu:** {m.status_summary}",
                f"- **24-48 Saat İçinde Doğum Beklenen İnekler:** {m.cows_in_24h_calving_window} Baş | **Aktif Sancı:** {m.active_labors_count} Baş | **Distosi Alarmı:** {m.dystocia_emergencies_count} Baş",
                f"- **Dondurulmuş Kolostrum Bankası:** `{m.colostrum_bank_stock_liters} Litre` (-20°C Üstün Kalite >%22 Brix Rezervi)",
                f"- **Buzağıhane Varlığı:** {m.nursery_calves_count} Baş Buzağı (Ortalama Vigor Skoru: {m.avg_calf_vigor_score}/10)"
            ])
            for t in m.calving_twins:
                calv_status = t.dystocia_assessment.alert_level
                status_icon = "🚨" if calv_status == "CRITICAL_DYSTOCIA_ALARM" else ("👀" if t.dystocia_assessment.stage == "STAGE_1_CERVIX_DILATION" else "✅")
                lines.append(
                    f"  - {status_icon} **{t.cow_name} (`{t.cow_id}`):** Evre: `{t.dystocia_assessment.stage}` | Sıcaklık: {t.telemetry.body_temperature_c:.2f}°C (ΔT: -{t.telemetry.temp_drop_c:.2f}°C) | Kuyruk Açısı: {t.telemetry.tail_tilt_angle_deg}° ({t.telemetry.tail_raising_frequency_per_hr} sancı/saat) | {t.dystocia_assessment.recommended_action}"
                )
                if t.colostrum:
                    lines.append(f"    - 🍼 *Kolostrum Refraktometresi:* %{t.colostrum.brix_refractometer_pct:.1f} Brix ({t.colostrum.igg_concentration_g_per_l:.1f} g/L IgG) - Kalite: `{t.colostrum.quality_grade}`")
                if t.calf:
                    lines.append(f"    - 🐮 *Yeni Doğan Buzağı:* `{t.calf.calf_id}` ({t.calf.gender}, {t.calf.birth_weight_kg} kg) - Vigor: {t.calf.vigor_apgar_score_1_10}/10 | STP: {t.calf.serum_total_protein_g_dl} g/dL")

        lines.extend([
            "",
            "---",
            "## 4. 🌱 RuFaS & IPCC Karbon ve Metan Emisyon Tablosu",
            f"- **Günlük Toplam Enterik Metan:** `{state.sustainability.total_daily_methane_kg} kg CH₄`",
            f"- **Toplam Karbon Ayak İzi:** `{state.sustainability.total_co2e_kg} kg CO₂e / gün`",
            f"- **Metan Yoğunluğu:** `{state.sustainability.avg_methane_intensity} g CH₄ / kg süt`",
            f"- **Yemden Yararlanma (FCR):** `{state.sustainability.feed_conversion_efficiency} kg Süt / kg DMI`",
            "",
            "---",
            "## 5. 🧬 Genomik Seleksiyon, Pedigri & Akıllı Çiftleştirme",
        ])

        if state.genomics:
            g = state.genomics
            lines.extend([
                f"- **Genotiplenen Sürü Varlığı:** {g.total_genotyped_cows} Baş | **Ortalama Net Merit:** `${g.avg_herd_net_merit:,.0f} NM$`",
                f"- **Sürü Akrabalık Düzeyi:** `%{g.avg_herd_inbreeding_pct:.2f} F` (Kritik Eşik: <%6.25 Güvenli)",
                f"- **Elit Dişi Damızlıklar:** {g.elite_donors_count} Baş | **Katalog Boğa Sayısı:** {g.available_catalog_bulls_count} Elit Boğa",
                "",
                "| Küpe | İsim | Pedigri (Baba x Anne Babası) | Net Merit | Inbreeding F | Önerilen 1. Boğa | Yavru Tahmini NM$ / F |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
            ])
            for a in state.animals:
                if a.pedigree:
                    ped = a.pedigree
                    top_m = g.mating_matrix_recommendations.get(a.id, [None])[0]
                    rec_str = f"{top_m.bull.bull_name}" if top_m else "-"
                    yavru_str = f"${top_m.expected_progeny_net_merit:,.0f} / %{top_m.progeny_inbreeding_f_pct:.1f}" if top_m else "-"
                    lines.append(
                        f"| `{a.id}` | {a.name} | {ped.sire_name} x {ped.maternal_grand_sire_name} | ${ped.gebv.net_merit_dollars:,.0f} | %{ped.individual_inbreeding_coeff_f_pct:.1f} | {rec_str} | {yavru_str} |"
                    )

        lines.extend([
            "",
            "---",
            "## 6. 💰 Finansal & ROI Tablosu (80 Baş Ölçekli Projeksiyon)",
            f"- **Günlük Brüt Süt Geliri:** {state.financials.daily_gross_milk_revenue:,.2f} TL",
            f"- **Günlük Yem Gideri:** {state.financials.daily_total_feed_cost:,.2f} TL",
            f"- **Yem Üzeri Günlük Net Gelir (IOFC):** {state.financials.daily_net_margin_over_feed:,.2f} TL",
            f"- **Aylık Net Dijital İkiz Tasarrufu:** {state.financials.total_monthly_net_benefit:,.2f} TL/ay",
            f"- **Yatırım Geri Dönüşü (Payback Süresi):** **{state.financials.estimated_payback_period_years:.1f} Yıl**",
            "",
            "> Bu rapor AgriTwin Digital Twin Core v2 tarafından ICAR ADE ve inSiliCow standartlarında otomatik derlenmiştir."
        ])

        return "\n".join(lines)

if __name__ == "__main__":
    print(FarmAuditReportGenerator.generate_daily_audit_markdown())
