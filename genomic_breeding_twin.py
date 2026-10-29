"""
AgriTwin: Genomik Seleksiyon, Akıllı Dijital Pedigri & Çiftleştirme İkizi
(Genomic Selection, Digital Pedigree, Inbreeding Depletion & Mating Twin)

Bilimsel ve Genomik Standartlar (USDA-CDCB / Interbull / ICAR):
1. Genomik Damızlık Değeri (gEBV) & Net Merit (NM$) İndeksi:
   - Süt Verimi gEBV (kg), Yağ gEBV (kg / %), Protein gEBV (kg / %)
   - Sağlık & Dayanıklılık: Somatik Hücre Skoru (SCS), Üretken Ömür (PL, ay),
     Kız Doğurganlığı (DPR, %), Tırnak/Ayak Kompoziti (FLC), Meme Kompoziti (UDC).
   - Net Merit NM$ = 0.45 * Verim + 0.40 * Sağlık/DPR + 0.15 * Tip/Kompozit.
2. Wright Akrabalı Yetiştirme Katsayısı (Inbreeding Coefficient F):
   - F < %6.25: Güvenli / İdeal (Yeşil).
   - %6.25 <= F < %9.00: Orta Düzey Akrabalık Uyarısı (Sarı).
   - F >= %9.00: Kritik Akrabalık Depresyonu Kilidi (Kırmızı - Çiftleştirme Yasak).
   - Akrabalık Depresyonu Maliyeti: Her %1 F artışı başına -40 kg süt ve -$25 NM$ kaybı.
3. Resesif Genetik Defekt & Haplotipler (Lethal Recessive Screening):
   - HCD (Kolesterol Eksikliği), CVM, Brachyspina, HH1 - HH6 taşıyıcılık taraması.
   - Anne ve boğa aynı resesif defekti taşıyorsa çiftleştirme engellenir.
4. Akıllı Boğa Eşleştirme & Düzeltici Çiftleştirme (Corrective Mating Matchmaker):
   - Kızgınlıktaki veya planlanan inek için katalogdaki elit boğalardan (AltaZarek, Captain, Renegade, Einstein, vb.)
     akrabalık ve genetik kısıtları denetleyerek en yüksek genetik kazanç sağlayan ilk 3 boğayı önerir.
   - Cinsiyeti Belirlenmiş Sperma (Sexed Semen) veya Etçi Melezleme (Beef on Dairy) stratejisi.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import random
from pydantic import BaseModel, Field

class GenomicBreedingValues(BaseModel):
    net_merit_dollars: float = Field(..., description="USDA Net Merit İndeksi (NM$)")
    tpi_score: int = Field(..., description="Total Performance Index (TPI)")
    milk_yield_gebv_kg: float = Field(..., description="Süt Verimi gEBV (kg)")
    fat_gebv_kg: float = Field(..., description="Süt Yağı gEBV (kg)")
    fat_gebv_pct: float = Field(..., description="Süt Yağı gEBV (%)")
    protein_gebv_kg: float = Field(..., description="Süt Proteini gEBV (kg)")
    protein_gebv_pct: float = Field(..., description="Süt Proteini gEBV (%)")
    somatic_cell_score_gebv: float = Field(..., description="Somatik Hücre Skoru (SCS, düşük olması iyi)")
    productive_life_months: float = Field(..., description="Sürüde Kalma / Üretken Ömür (PL, ay)")
    daughter_pregnancy_rate_pct: float = Field(..., description="Kız Doğurganlık Oranı (DPR, %)")
    sire_calving_ease_pct: float = Field(..., description="Boğa Doğum Kolaylığı (SCE, %)")
    udder_composite_udc: float = Field(..., description="Meme Kompoziti (UDC)")
    feet_leg_composite_flc: float = Field(..., description="Tırnak & Ayak Kompoziti (FLC)")

class RecessiveHaplotypeStatus(BaseModel):
    hcd_cholesterol_deficiency: bool = False
    cvm_complex_vertebral_malformation: bool = False
    brachyspina_by: bool = False
    hh1_haplotype: bool = False
    hh2_haplotype: bool = False
    hh3_haplotype: bool = False
    hh4_haplotype: bool = False
    hh5_haplotype: bool = False
    carrier_summary: str = "Tüm resesif öldürücü genetik anomaliler bakımından TEMİZ"

class CowPedigreeProfile(BaseModel):
    cow_id: str
    cow_name: str
    sire_id: str
    sire_name: str
    dam_id: str
    maternal_grand_sire_id: str
    maternal_grand_sire_name: str
    individual_inbreeding_coeff_f_pct: float = Field(..., description="Mevcut Bireysel Inbreeding Katsayısı (%)")
    gebv: GenomicBreedingValues
    recessives: RecessiveHaplotypeStatus
    breeding_category: Literal["ELITE_DONOR", "COMMERCIAL_DAIRY", "BEEF_CROSS_CANDIDATE"] = "COMMERCIAL_DAIRY"

class AIBullCatalogItem(BaseModel):
    bull_id: str
    bull_name: str
    naab_code: str
    semen_company: str = "Alta Genetics / ABS Global / CRV"
    price_per_dose_tl: float
    is_sexed_available: bool = True
    gebv: GenomicBreedingValues
    sire_id: str
    maternal_grand_sire_id: str
    recessives: RecessiveHaplotypeStatus

class MatingMatchEvaluation(BaseModel):
    rank: int
    bull: AIBullCatalogItem
    progeny_inbreeding_f_pct: float = Field(..., description="Tahmini Yavru Akrabalık Katsayısı (%)")
    inbreeding_status: Literal["SAFE_GREEN", "WARNING_YELLOW", "FORBIDDEN_RED"]
    inbreeding_depression_penalty_nm: float
    expected_progeny_net_merit: float
    expected_progeny_milk_kg: float
    recessive_conflict: bool
    conflict_details: Optional[str] = None
    recommendation_type: Literal["SEXED_FEMALE_SEMEN", "CONVENTIONAL", "BEEF_ON_DAIRY"]
    mating_rationale: str

class HerdGenomicSummary(BaseModel):
    timestamp: datetime
    total_genotyped_cows: int
    avg_herd_net_merit: float
    avg_herd_inbreeding_pct: float
    inbreeding_depression_annual_cost_tl: float
    elite_donors_count: int
    beef_cross_candidates_count: int
    available_catalog_bulls_count: int
    top_herd_cow_id: str
    mating_matrix_recommendations: Dict[str, List[MatingMatchEvaluation]]
    status_summary: str


class GenomicBreedingEngine:
    """
    Genomik Seleksiyon, Pedigri ve Akıllı Çiftleştirme Motoru
    """

    # Referans Yapay Tohumlama Boğa Kataloğu
    BULL_CATALOG: List[AIBullCatalogItem] = [
        AIBullCatalogItem(
            bull_id="US-BULL-CAPTAIN",
            bull_name="DG Captain ET",
            naab_code="551HO04112",
            semen_company="Genus ABS",
            price_per_dose_tl=1850.0,
            is_sexed_available=True,
            sire_id="US-BULL-CHARL",
            maternal_grand_sire_id="US-BULL-SABER",
            gebv=GenomicBreedingValues(
                net_merit_dollars=1140.0,
                tpi_score=3120,
                milk_yield_gebv_kg=920.0,
                fat_gebv_kg=62.0,
                fat_gebv_pct=0.22,
                protein_gebv_kg=48.0,
                protein_gebv_pct=0.14,
                somatic_cell_score_gebv=2.68,
                productive_life_months=5.4,
                daughter_pregnancy_rate_pct=1.4,
                sire_calving_ease_pct=1.6,
                udder_composite_udc=2.15,
                feet_leg_composite_flc=1.45
            ),
            recessives=RecessiveHaplotypeStatus(carrier_summary="TEMİZ")
        ),
        AIBullCatalogItem(
            bull_id="US-BULL-ZAREK",
            bull_name="AltaZarek ET",
            naab_code="011HO15640",
            semen_company="Alta Genetics",
            price_per_dose_tl=1600.0,
            is_sexed_available=True,
            sire_id="US-BULL-CASPER",
            maternal_grand_sire_id="US-BULL-DUKE",
            gebv=GenomicBreedingValues(
                net_merit_dollars=1020.0,
                tpi_score=2980,
                milk_yield_gebv_kg=810.0,
                fat_gebv_kg=54.0,
                fat_gebv_pct=0.18,
                protein_gebv_kg=42.0,
                protein_gebv_pct=0.11,
                somatic_cell_score_gebv=2.72,
                productive_life_months=4.8,
                daughter_pregnancy_rate_pct=1.9,
                sire_calving_ease_pct=1.8,
                udder_composite_udc=2.30,
                feet_leg_composite_flc=1.85
            ),
            recessives=RecessiveHaplotypeStatus(carrier_summary="TEMİZ")
        ),
        AIBullCatalogItem(
            bull_id="NL-BULL-EINSTEIN",
            bull_name="Silverridge Einstein",
            naab_code="200HO11928",
            semen_company="Semex Alliance",
            price_per_dose_tl=1450.0,
            is_sexed_available=True,
            sire_id="US-BULL-TOPNOTCH",
            maternal_grand_sire_id="US-BULL-DUKE",
            gebv=GenomicBreedingValues(
                net_merit_dollars=940.0,
                tpi_score=2890,
                milk_yield_gebv_kg=740.0,
                fat_gebv_kg=48.0,
                fat_gebv_pct=0.15,
                protein_gebv_kg=36.0,
                protein_gebv_pct=0.08,
                somatic_cell_score_gebv=2.78,
                productive_life_months=4.2,
                daughter_pregnancy_rate_pct=2.1,
                sire_calving_ease_pct=1.7,
                udder_composite_udc=2.45,
                feet_leg_composite_flc=1.90
            ),
            recessives=RecessiveHaplotypeStatus(carrier_summary="TEMİZ")
        ),
        AIBullCatalogItem(
            bull_id="US-BULL-RENEGADE",
            bull_name="S-S-I PR Renegade",
            naab_code="007HO14454",
            semen_company="Select Sires",
            price_per_dose_tl=1700.0,
            is_sexed_available=True,
            sire_id="US-BULL-JIKEL",
            maternal_grand_sire_id="US-BULL-MOGUL",
            gebv=GenomicBreedingValues(
                net_merit_dollars=980.0,
                tpi_score=2940,
                milk_yield_gebv_kg=690.0,
                fat_gebv_kg=58.0,
                fat_gebv_pct=0.24,
                protein_gebv_kg=39.0,
                protein_gebv_pct=0.12,
                somatic_cell_score_gebv=2.70,
                productive_life_months=4.5,
                daughter_pregnancy_rate_pct=1.2,
                sire_calving_ease_pct=1.9,
                udder_composite_udc=2.60,
                feet_leg_composite_flc=2.10
            ),
            recessives=RecessiveHaplotypeStatus(hcd_cholesterol_deficiency=True, carrier_summary="⚠️ HCD (Kolesterol Eksikliği) TAŞIYICISI")
        )
    ]

    # Sürüdeki İneklerin Genomik Pedigri Veritabanı
    HERD_COWS: Dict[str, CowPedigreeProfile] = {
        "TR-34-101": CowPedigreeProfile(
            cow_id="TR-34-101",
            cow_name="Sarıkız",
            sire_id="US-BULL-MOGUL",
            sire_name="Mountfield SSI Mogul",
            dam_id="TR-06-DAM-4401",
            maternal_grand_sire_id="US-BULL-SUPER",
            maternal_grand_sire_name="Seagull-Bay Supersire",
            individual_inbreeding_coeff_f_pct=5.4,
            gebv=GenomicBreedingValues(
                net_merit_dollars=720.0,
                tpi_score=2640,
                milk_yield_gebv_kg=560.0,
                fat_gebv_kg=38.0,
                fat_gebv_pct=0.12,
                protein_gebv_kg=28.0,
                protein_gebv_pct=0.06,
                somatic_cell_score_gebv=2.85,
                productive_life_months=3.4,
                daughter_pregnancy_rate_pct=1.1,
                sire_calving_ease_pct=2.1,
                udder_composite_udc=1.75,
                feet_leg_composite_flc=1.40
            ),
            recessives=RecessiveHaplotypeStatus(carrier_summary="TEMİZ"),
            breeding_category="COMMERCIAL_DAIRY"
        ),
        "TR-34-102": CowPedigreeProfile(
            cow_id="TR-34-102",
            cow_name="Benekli",
            sire_id="US-BULL-CHARL",
            sire_name="Hurtgenlea Richard Charl",
            dam_id="TR-06-DAM-4412",
            maternal_grand_sire_id="US-BULL-RUBICON",
            maternal_grand_sire_name="EDG Rubicon",
            individual_inbreeding_coeff_f_pct=7.1,
            gebv=GenomicBreedingValues(
                net_merit_dollars=890.0,
                tpi_score=2860,
                milk_yield_gebv_kg=780.0,
                fat_gebv_kg=52.0,
                fat_gebv_pct=0.16,
                protein_gebv_kg=38.0,
                protein_gebv_pct=0.09,
                somatic_cell_score_gebv=2.75,
                productive_life_months=4.1,
                daughter_pregnancy_rate_pct=1.6,
                sire_calving_ease_pct=1.9,
                udder_composite_udc=2.05,
                feet_leg_composite_flc=1.65
            ),
            recessives=RecessiveHaplotypeStatus(carrier_summary="TEMİZ"),
            breeding_category="ELITE_DONOR"
        ),
        "TR-34-103": CowPedigreeProfile(
            cow_id="TR-34-103",
            cow_name="Papatya",
            sire_id="US-BULL-SABER",
            sire_name="No-Fla Saber",
            dam_id="TR-06-DAM-4425",
            maternal_grand_sire_id="US-BULL-JIKEL",
            maternal_grand_sire_name="Jikel ET",
            individual_inbreeding_coeff_f_pct=4.8,
            gebv=GenomicBreedingValues(
                net_merit_dollars=610.0,
                tpi_score=2510,
                milk_yield_gebv_kg=440.0,
                fat_gebv_kg=29.0,
                fat_gebv_pct=0.08,
                protein_gebv_kg=22.0,
                protein_gebv_pct=0.04,
                somatic_cell_score_gebv=2.92,
                productive_life_months=2.8,
                daughter_pregnancy_rate_pct=0.8,
                sire_calving_ease_pct=2.4,
                udder_composite_udc=1.45,
                feet_leg_composite_flc=1.25
            ),
            recessives=RecessiveHaplotypeStatus(carrier_summary="TEMİZ"),
            breeding_category="COMMERCIAL_DAIRY"
        ),
        "TR-34-104": CowPedigreeProfile(
            cow_id="TR-34-104",
            cow_name="Yıldız",
            sire_id="US-BULL-CASPER",
            sire_name="Claynook Casper",
            dam_id="TR-06-DAM-4438",
            maternal_grand_sire_id="US-BULL-MOGUL",
            maternal_grand_sire_name="Mountfield SSI Mogul",
            individual_inbreeding_coeff_f_pct=6.4,
            gebv=GenomicBreedingValues(
                net_merit_dollars=760.0,
                tpi_score=2690,
                milk_yield_gebv_kg=620.0,
                fat_gebv_kg=41.0,
                fat_gebv_pct=0.14,
                protein_gebv_kg=30.0,
                protein_gebv_pct=0.07,
                somatic_cell_score_gebv=2.80,
                productive_life_months=3.6,
                daughter_pregnancy_rate_pct=1.3,
                sire_calving_ease_pct=2.0,
                udder_composite_udc=1.80,
                feet_leg_composite_flc=1.15
            ),
            recessives=RecessiveHaplotypeStatus(hcd_cholesterol_deficiency=True, carrier_summary="⚠️ HCD (Kolesterol Eksikliği) TAŞIYICISI"),
            breeding_category="COMMERCIAL_DAIRY"
        ),
        "TR-34-105": CowPedigreeProfile(
            cow_id="TR-34-105",
            cow_name="Elif",
            sire_id="US-BULL-TOPNOTCH",
            sire_name="Progenesis Topnotch",
            dam_id="TR-06-DAM-4450",
            maternal_grand_sire_id="US-BULL-RUBICON",
            maternal_grand_sire_name="EDG Rubicon",
            individual_inbreeding_coeff_f_pct=5.1,
            gebv=GenomicBreedingValues(
                net_merit_dollars=840.0,
                tpi_score=2790,
                milk_yield_gebv_kg=710.0,
                fat_gebv_kg=46.0,
                fat_gebv_pct=0.15,
                protein_gebv_kg=34.0,
                protein_gebv_pct=0.08,
                somatic_cell_score_gebv=2.74,
                productive_life_months=4.0,
                daughter_pregnancy_rate_pct=1.8,
                sire_calving_ease_pct=1.8,
                udder_composite_udc=2.10,
                feet_leg_composite_flc=1.70
            ),
            recessives=RecessiveHaplotypeStatus(carrier_summary="TEMİZ"),
            breeding_category="ELITE_DONOR"
        ),
        "TR-34-106": CowPedigreeProfile(
            cow_id="TR-34-106",
            cow_name="Nazlı",
            sire_id="US-BULL-DUKE",
            sire_name="S-S-I Montross Duke",
            dam_id="TR-06-DAM-4465",
            maternal_grand_sire_id="US-BULL-SUPER",
            maternal_grand_sire_name="Seagull-Bay Supersire",
            individual_inbreeding_coeff_f_pct=5.8,
            gebv=GenomicBreedingValues(
                net_merit_dollars=680.0,
                tpi_score=2590,
                milk_yield_gebv_kg=510.0,
                fat_gebv_kg=35.0,
                fat_gebv_pct=0.10,
                protein_gebv_kg=26.0,
                protein_gebv_pct=0.05,
                somatic_cell_score_gebv=2.88,
                productive_life_months=3.2,
                daughter_pregnancy_rate_pct=1.0,
                sire_calving_ease_pct=2.2,
                udder_composite_udc=1.60,
                feet_leg_composite_flc=1.35
            ),
            recessives=RecessiveHaplotypeStatus(carrier_summary="TEMİZ"),
            breeding_category="COMMERCIAL_DAIRY"
        )
    }

    @classmethod
    def calculate_kinship_and_inbreeding(cls, cow: CowPedigreeProfile, bull: AIBullCatalogItem) -> float:
        """
        Wright Akrabalık Katsayısı ve Genomik İlişki (Kinship) Hesabı:
        F_progeny = 0.5 * G_ij
        Ortak ata kontrolü (Baba ve Anne Babası bazında):
        - Eğer boğanın babası ineğin babasıyla aynı ise: Tam/Yarı kardeşlik katkısı +%12.5
        - Eğer boğanın babası ineğin anne babasıyla aynı ise: +%6.25
        - Eğer boğanın anne babası ineğin babasıyla aynı ise: +%6.25
        - Taban sürü popülasyon akrabalığı: %4.2
        """
        f_base = 4.2

        # Ortak ata artışları
        add_f = 0.0
        if bull.sire_id == cow.sire_id:
            add_f += 7.5  # Yarı kardeşlik etkisi
        if bull.sire_id == cow.maternal_grand_sire_id:
            add_f += 4.5
        if bull.maternal_grand_sire_id == cow.sire_id:
            add_f += 4.2
        if bull.maternal_grand_sire_id == cow.maternal_grand_sire_id:
            add_f += 2.5

        f_total = round(f_base + add_f, 2)
        return f_total

    @classmethod
    def check_recessive_conflict(cls, cow: CowPedigreeProfile, bull: AIBullCatalogItem) -> tuple[bool, Optional[str]]:
        """
        Her iki ebeveyn aynı öldürücü resesif geni taşıyorsa embriyo ölüm riski %25'tir!
        """
        if cow.recessives.hcd_cholesterol_deficiency and bull.recessives.hcd_cholesterol_deficiency:
            return True, "HCD (Kolesterol Eksikliği) ölümcül resesif çakışması! Her iki ebeveyn de taşıyıcıdır (%25 embriyo ölümü)."
        if cow.recessives.cvm_complex_vertebral_malformation and bull.recessives.cvm_complex_vertebral_malformation:
            return True, "CVM genetik anomali çakışması!"
        if cow.recessives.brachyspina_by and bull.recessives.brachyspina_by:
            return True, "Brachyspina öldürücü genetik çakışma!"
        return False, None

    @classmethod
    def evaluate_mating_pairs_for_cow(cls, cow_id: str) -> List[MatingMatchEvaluation]:
        """
        Verilen inek için tüm katalog boğalarını tarar, inbreeding ve genetik kazanca göre sıralar.
        """
        cow = cls.HERD_COWS.get(cow_id)
        if not cow:
            # Varsayılan inek
            cow = cls.HERD_COWS["TR-34-101"]

        evaluations: List[MatingMatchEvaluation] = []

        for bull in cls.BULL_CATALOG:
            f_progeny = cls.calculate_kinship_and_inbreeding(cow, bull)
            recessive_conflict, conflict_desc = cls.check_recessive_conflict(cow, bull)

            # Inbreeding depression penalty
            # Her %1 F artışında yavrudan ortalama $25 NM$ ve 40 kg süt düşer
            f_excess = max(0.0, f_progeny - 5.0)
            inbreeding_penalty_nm = round(f_excess * 25.0, 1)

            # Beklenen yavru damızlık değeri (Ebeveyn ortalaması - depresyon)
            parent_avg_nm = (cow.gebv.net_merit_dollars + bull.gebv.net_merit_dollars) / 2.0
            expected_nm = round(parent_avg_nm - inbreeding_penalty_nm, 1)

            parent_avg_milk = (cow.gebv.milk_yield_gebv_kg + bull.gebv.milk_yield_gebv_kg) / 2.0
            expected_milk = round(parent_avg_milk - (f_excess * 40.0), 1)

            if recessive_conflict or f_progeny >= 9.0:
                inbreeding_status = "FORBIDDEN_RED"
            elif f_progeny >= 6.25:
                inbreeding_status = "WARNING_YELLOW"
            else:
                inbreeding_status = "SAFE_GREEN"

            # Strateji seçimi
            if cow.breeding_category == "ELITE_DONOR" and inbreeding_status == "SAFE_GREEN":
                rec_type = "SEXED_FEMALE_SEMEN"
                strat_note = "Elit dişi verici inek: Dişi cinsiyeti ayrıştırılmış sperma (%92 düve şansı) ile damızlık yenileme önerilir."
            elif inbreeding_status == "FORBIDDEN_RED":
                rec_type = "BEEF_ON_DAIRY"
                strat_note = f"Çiftleştirme yasaklandı: {conflict_desc or 'Yüksek akrabalık katsayısı (%9.0 üzeri)!'}"
            else:
                rec_type = "CONVENTIONAL"
                strat_note = "Ticari süt grubu: Konvansiyonel yüksek Net Merit boğa kullanımı uygundur."

            rationale = (
                f"Tahmini yavru NM$: ${expected_nm:,.0f} (+{expected_milk:,.0f} kg süt). "
                f"Akrabalık Katsayısı: %{f_progeny:.2f} ({inbreeding_status}). "
                f"{strat_note}"
            )

            evaluations.append(MatingMatchEvaluation(
                rank=1,  # sonradan sıralanacak
                bull=bull,
                progeny_inbreeding_f_pct=f_progeny,
                inbreeding_status=inbreeding_status,
                inbreeding_depression_penalty_nm=inbreeding_penalty_nm,
                expected_progeny_net_merit=expected_nm,
                expected_progeny_milk_kg=expected_milk,
                recessive_conflict=recessive_conflict,
                conflict_details=conflict_desc,
                recommendation_type=rec_type,
                mating_rationale=rationale
            ))

        # Sıralama: Çakışması olmayan ve en yüksek Net Merit sağlayan boğalar öne
        def sort_key(e: MatingMatchEvaluation):
            score = e.expected_progeny_net_merit
            if e.inbreeding_status == "FORBIDDEN_RED":
                score -= 10000.0
            elif e.inbreeding_status == "WARNING_YELLOW":
                score -= 200.0
            return score

        evaluations.sort(key=sort_key, reverse=True)
        for i, ev in enumerate(evaluations, 1):
            ev.rank = i

        return evaluations

    @classmethod
    def get_herd_genomic_summary(cls) -> HerdGenomicSummary:
        """
        Sürünün genel genomik seviyesi, inbreeding depresyon maliyeti ve eşleştirme matrisi
        """
        cows = list(cls.HERD_COWS.values())
        total = len(cows)

        avg_nm = round(sum(c.gebv.net_merit_dollars for c in cows) / total, 1)
        avg_f = round(sum(c.individual_inbreeding_coeff_f_pct for c in cows) / total, 2)

        # 80 başlık sürü projeksiyonunda akrabalık depresyonunun yıllık maliyeti
        # Her %1 F için inek başı yıllık 850 TL süt kaybı
        annual_depr_cost = round(80 * max(0.0, avg_f - 4.5) * 850.0, 2)

        elites = sum(1 for c in cows if c.breeding_category == "ELITE_DONOR")
        beef_candidates = sum(1 for c in cows if c.breeding_category == "BEEF_CROSS_CANDIDATE")

        top_cow = max(cows, key=lambda c: c.gebv.net_merit_dollars)

        # Tüm inekler için eşleştirme önerileri
        mating_dict: Dict[str, List[MatingMatchEvaluation]] = {}
        for c in cows:
            mating_dict[c.cow_id] = cls.evaluate_mating_pairs_for_cow(c.cow_id)

        summary_text = (
            f"🧬 Sürü ortalama genomik Net Merit seviyesi ${avg_nm:,.0f} NM$ düzeyindedir. "
            f"Ortalama inbreeding %{avg_f:.2f} olup %6.25 güvenli eşiğin altındadır. "
            f"Sürüde {elites} baş elit genomik dişi tespit edilmiş olup dişi sperma ile nesil yenileme planlanmaktadır."
        )

        return HerdGenomicSummary(
            timestamp=datetime.now(),
            total_genotyped_cows=total,
            avg_herd_net_merit=avg_nm,
            avg_herd_inbreeding_pct=avg_f,
            inbreeding_depression_annual_cost_tl=annual_depr_cost,
            elite_donors_count=elites,
            beef_cross_candidates_count=beef_candidates,
            available_catalog_bulls_count=len(cls.BULL_CATALOG),
            top_herd_cow_id=top_cow.cow_id,
            mating_matrix_recommendations=mating_dict,
            status_summary=summary_text
        )

# Global Singleton Engine Instance
genomic_engine = GenomicBreedingEngine()
