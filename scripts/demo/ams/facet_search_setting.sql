--
-- PostgreSQL database dump
--

-- Dumped from database version 12.22 (Debian 12.22-1.pgdg120+1)
-- Dumped by pg_dump version 12.22 (Debian 12.22-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: facet_search_setting; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.facet_search_setting (id, name_en, name_jp, mapping, aggregations, active, ui_type, display_number, is_open, search_condition) VALUES
(51001, 'genre_filter', 'データセットの分野', 'text1.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51002, 'subjectOf_filter', 'データセットの名称', 'title', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51003, 'payOrFree_filter', '有償・無償', 'text2.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51004, 'contactPermission_filter', '連絡・許諾の要不要', 'text3.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51005, 'creator_filter', 'データ作成者 氏名', 'creator.creatorName', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51006, 'projectName_filter', 'プロジェクト名', 'text5.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51007, 'iCIsNo_filter', '（IC無の場合）', 'text6.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51008, 'accessMode_filter', 'アクセス権', 'text7.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51009, 'informedConsent_filter', '（ヒト）インフォームドコンセント（IC） 有・無・不要', 'text8.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51010, 'dataId_filter', 'データID', 'text4.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51011, 'analysisType_filter', '解析対象データ', 'text9.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51012, 'creativeWorkStatus_filter', 'データ作成者 所属', 'creator.affiliation.affiliationName', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51013, 'creatorMail_filter', 'データ作成者 連絡先', 'text10.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51014, 'belongingOfDataManager_filter', 'データ管理者 所属', 'contributor.affiliation.affiliationName', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51015, 'nameOfDataManager_filter', 'データ管理者 氏名', 'text11.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51016, 'contributorMail_filter', 'データ管理者 連絡先', 'text12.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51017, 'license_filter', 'ライセンス', 'text13.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51018, 'presenceOfMetadataFiles_filter', 'モダリティ用メタデータファイルの有無', 'text14.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51019, 'acknowledgments_filter', '謝辞に記載の要不要', 'text15.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51020, 'commercialUse_filter', '商用利用の可否', 'text16.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51021, 'repositoryInfo_filter', 'リポジトリ情報', 'text17.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51022, 'thirdParty_filter', '（IC有の場合）第三者提供の同意', 'text18.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51023, 'offerings_filter', '（IC有の場合）海外提供', 'text19.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51024, 'industrialUse_filter', '（IC有の場合）産業利用等', 'text20.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51025, 'anonymousProcessing_filter', '（ヒト）匿名加工の有無', 'text21.raw', '[]', true, 'CheckboxList', 5, true, 'OR'),
(51026, 'conflictOfInterest_filter', '利益相反の有無', 'text22.raw', '[]', true, 'CheckboxList', 5, true, 'OR')
ON CONFLICT (id) DO UPDATE SET
  id = EXCLUDED.id,
  name_en = EXCLUDED.name_en,
  name_jp = EXCLUDED.name_jp,
  mapping = EXCLUDED.mapping,
  aggregations = EXCLUDED.aggregations,
  active = EXCLUDED.active,
  ui_type = EXCLUDED.ui_type,
  display_number = EXCLUDED.display_number,
  is_open = EXCLUDED.is_open,
  search_condition = EXCLUDED.search_condition;



--
-- Name: facet_search_setting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

--
-- PostgreSQL database dump complete
--
