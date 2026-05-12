# Transcript: https://www.youtube.com/watch?v=SJEnb5cadyo

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 606

---

**[00:03]** [music]  
**[00:08]** Hello everyone and welcome. Today we  
**[00:12]** have graph rag for law building legal  
**[00:15]** reasoning agents with Neo4j and LLMs.  
**[00:19]** And today we have um Alexander Kasov and  
**[00:23]** we'll hand it over to him.  
**[00:26]** >> Uh hello everyone. Thank you for joining  
**[00:29]** the session and I will um definitely uh  
**[00:34]** explain how to structure the law using  
**[00:37]** nail and use it for LLMs uh to get the  
**[00:43]** consistently  
**[00:45]** traceable explainable results. uh so as  
**[00:50]** uh I have 20 years of experience as a as  
**[00:54]** a practicing lawyer and 10 years as the  
**[00:57]** legal tech developer uh and um to uh two  
**[01:03]** degrees in that in that field. So I  
**[01:05]** combine my knowledge to deliver uh those  
**[01:08]** kind of products using my um uh law  
**[01:12]** practice experience uh to structure the  
**[01:15]** uh software properly to to to deliver  
**[01:19]** precise results. So uh why should we u  
**[01:24]** use graph for for for structuring the  
**[01:27]** law? The problem is that u uh uh regular  
**[01:31]** raw LLM is is is not good for um  
**[01:37]** answering legal questions. Why? Because  
**[01:40]** um even though um LLM may be  
**[01:43]** self-confident  
**[01:45]** but they not not regularly uh produce  
**[01:50]** uh traceable results.  
**[01:53]** [clears throat]  
**[01:53]** Why? because hallucinations  
**[01:56]** um may may be caused by static training  
**[01:58]** data, outdated law, uh no access to  
**[02:01]** private or or corporate by default. Uh  
**[02:05]** and um classic rack helps to uh retrieve  
**[02:11]** passages and relationships.  
**[02:14]** Um  
**[02:17]** um connect statutes and and precedents  
**[02:19]** into graph showing how provisions  
**[02:21]** relate. uh on paragraphs uh regularly  
**[02:25]** represent one notes which uh eliminates  
**[02:28]** the problem of of the chunking and and  
**[02:31]** the uh hybrid retrieval allows us to uh  
**[02:35]** get the not only vector results but also  
**[02:39]** reversal and classification nodes as we  
**[02:42]** will see later. Uh also um  
**[02:48]** uh our plan for for this session is to  
**[02:51]** um e explore how mo how to model legal  
**[02:56]** entities and relationships as a graph.  
**[02:58]** [snorts] uh augment those uh this those  
**[03:01]** graph layer with vector and  
**[03:03]** classification layers and assembled 3D  
**[03:06]** context to um to construct  
**[03:12]** comprehensive context for the LMS.  
**[03:15]** uh if we will have time uh I will  
**[03:18]** represent um live demo at at our website  
**[03:22]** and um some  
**[03:25]** answer answer some questions.  
**[03:28]** So uh first let let me introduce the two  
**[03:31]** two general patterns in constructing  
**[03:33]** graph racks. Uh one of those uh as as we  
**[03:39]** believe is a is a graph on ephemeral  
**[03:41]** graph on the fly and the other is  
**[03:43]** pre-built. Those are two partners are  
**[03:46]** are different in their purpose because  
**[03:50]** first of all uh on the fly on the fly uh  
**[03:54]** graph racks allows for um  
**[03:58]** for quicker results when using smaller  
**[04:01]** set of documents and uh uh pre-built  
**[04:05]** graph allows us to invest up front to to  
**[04:10]** construct the full corpus of model like  
**[04:12]** legit full full base of legislation and  
**[04:16]** so on.  
**[04:18]** Let me uh stop a little bit more in  
**[04:21]** details on on that session on on that uh  
**[04:23]** slide to better explain the advantages  
**[04:27]** and disadvantages of uh each um  
**[04:31]** of each uh type of of graph rack build.  
**[04:35]** Uh first of all um on the fly graphs  
**[04:39]** graph racks um can be uh very very quick  
**[04:44]** to compose. Uh they are they're perfect  
**[04:47]** to answer ad hoc quick questions. Uh  
**[04:50]** they are very good in uh when you have  
**[04:54]** um  
**[04:56]** have a need to to to make the proof of  
**[04:59]** concept on of concept and so on. But uh  
**[05:03]** their lack of um um base knowledge they  
**[05:07]** can can be um very  
**[05:11]** uh epoch in in in matter of  
**[05:14]** >> [snorts]  
**[05:14]** >> uh data structures and so on. Uh  
**[05:18]** pre-built graphs on the other hand  
**[05:20]** allows us to construct the whole corpus  
**[05:23]** of legislation and uh uh demand very  
**[05:28]** massive u investments in uh in  
**[05:32]** constructing data data model in  
**[05:36]** um pre prelabberating  
**[05:39]** uh texts of legislation. extracting  
**[05:43]** concepts, extracting references which is  
**[05:46]** most important for uh for constructing  
**[05:49]** uh vert not not only vertical  
**[05:51]** hierarchical uh references but also uh  
**[05:55]** horizontal uh ages to to build the the  
**[05:59]** full scale graph and uh but this uh this  
**[06:05]** investments pays off uh because you you  
**[06:08]** you are getting auditable provenence you  
**[06:11]** can um perform deep classification  
**[06:15]** uh extracting  
**[06:17]** super uh super consistent and super  
**[06:20]** valuable knowledge from from those nodes  
**[06:24]** uh which is in most cases impossible  
**[06:26]** when you when you do some works on the  
**[06:29]** fly. Uh  
**[06:32]** sorry. So uh another issue is that uh  
**[06:38]** the the better approach is to use hybrid  
**[06:41]** bridge uh combining those two approaches  
**[06:44]** when you have um predefined data model  
**[06:48]** ontologies use um u metagraph as the uh  
**[06:53]** structure to map existing uh knowledge.  
**[06:58]** uh pre-built legislative corpus to get  
**[07:02]** the uh solid base. construct uh the  
**[07:08]** uh update uh uh pipeline and uh on top  
**[07:13]** of that construct the uh on the-fly user  
**[07:18]** documents pipeline which which allows to  
**[07:21]** elaborate uh user docs extract knowledge  
**[07:25]** from that those documents map those uh  
**[07:29]** those knowledge against existing um data  
**[07:33]** model and uh throw it against existing  
**[07:38]** legislative corpus. That approach would  
**[07:41]** bring us to absolutely amazing results  
**[07:45]** when you can not only uh extract  
**[07:49]** knowledge from user documents but also  
**[07:51]** compare those documents with the  
**[07:53]** existing legislative corpus and uh which  
**[07:56]** we called it uh early make early case  
**[07:59]** assessments when you can um uh  
**[08:04]** compare expectations of the client of  
**[08:07]** the of a lawyer. uh concerning their  
**[08:10]** their particular situation with existing  
**[08:13]** case law for example. So that that gives  
**[08:16]** us a a very um promising results and we  
**[08:20]** we are now working on constructing both  
**[08:23]** of those structures and uh trying to  
**[08:26]** implement this hybrid bridge. So uh the  
**[08:30]** next topic would be um data models and  
**[08:34]** how we structure the law in in our uh  
**[08:38]** solution. uh we um opt out for using u  
**[08:44]** ontologies uh and uh one of those are  
**[08:47]** fiber uh which is functional  
**[08:49]** requirements for biblioraphic records is  
**[08:53]** the uh very well-known  
**[08:56]** uh enacted also in the European Union as  
**[08:59]** the as a core for Eurolex uh knowledge  
**[09:02]** graph uh it uh explores  
**[09:06]** a chain of uh of um um of instances. The  
**[09:12]** the root instance is work. The second is  
**[09:16]** expression and there are two others  
**[09:19]** which we're not focused on right now.  
**[09:22]** The work represents intellectual work.  
**[09:25]** So it's the any law any case law any  
**[09:28]** document itself represents this work. uh  
**[09:31]** is is represented by by the work we now  
**[09:34]** you you can see the um simple graph  
**[09:37]** representing uh one act and expression  
**[09:40]** represents it's um uh it's a version one  
**[09:45]** of one of versions one of the uh um ways  
**[09:50]** um legislator or judge expresses its uh  
**[09:55]** this work. Uh so uh this is the the the  
**[10:01]** very convenient way to to work with  
**[10:03]** versioning when you when you have um  
**[10:07]** pretty um dynamic legisl legislation. it  
**[10:12]** it's not the case for the uh for the  
**[10:14]** legal precedents for case for court  
**[10:17]** decisions but with the acts with the  
**[10:19]** subsidiary legislation it's a really  
**[10:22]** matters because when you throw to LLM  
**[10:26]** context with the case law dated 15 years  
**[10:30]** ago and contemporary act it definitely  
**[10:35]** will lead to some hallucinations because  
**[10:38]** act may be might be changed for for that  
**[10:42]** 15 years. And so when you uh [snorts]  
**[10:46]** feed to LLM  
**[10:48]** parts of of legit of case law texts, you  
**[10:52]** you should uh compare those text or  
**[10:55]** accompany those those text with the uh  
**[10:59]** contemporary for that particular  
**[11:02]** decision uh act subsidiary legislation  
**[11:05]** in and any any other sources. Um so um  
**[11:10]** in in in that regard we're using uh what  
**[11:12]** we call matter expression and regular  
**[11:15]** expressions. Here you can see that this  
**[11:17]** this expression is is a current version  
**[11:19]** of the uh of the of this act and the  
**[11:22]** others are just um outdated versions uh  
**[11:26]** and the uh digits here represent the uh  
**[11:31]** the dates uh in unis. Uh so the other  
**[11:35]** interesting concept uh uh we use with um  
**[11:40]** uh modeling graph modeling law in our  
**[11:44]** graph is the ecomtosa  
**[11:46]** uh ontology or XML standard uh which is  
**[11:50]** also developed by uh Bolognia University  
**[11:55]** for uh for being used in um in in  
**[11:59]** European u legislative practices. Uh  
**[12:03]** actually it's it's a very um uh very  
**[12:07]** important step in in developing legal  
**[12:10]** tech in general because it allows us to  
**[12:13]** makes to make um markdowns inside uh  
**[12:19]** legal texts. So this is uh one one part  
**[12:22]** of a comment also represents hierarchy  
**[12:25]** uh uh where each particular document uh  
**[12:30]** is is being represented by different  
**[12:32]** structures because as you may understand  
**[12:35]** the uh case law the decision of the  
**[12:38]** court is is not cannot have have the  
**[12:42]** same structure as the as the law or as  
**[12:45]** the subsidiary legislation. So they have  
**[12:48]** basically different um sections,  
**[12:50]** different um blocks of of texts and and  
**[12:54]** so on. For example, the judge explains  
**[12:57]** um  
**[12:59]** background of the case, arguments of the  
**[13:01]** parties and the act in act legislators  
**[13:05]** uh usually follow their strict uh uh  
**[13:11]** hierarchy and strict schema to to  
**[13:15]** connect provisions. So uh each each of  
**[13:19]** those um uh structures are can be found  
**[13:23]** in a common tossa and we expired by that  
**[13:26]** anthology implemented that in our data  
**[13:29]** model. So you can see here those those  
**[13:32]** green big green node is the is the act  
**[13:36]** uh those are this is smaller one is the  
**[13:39]** subsidiary legislation.  
**[13:42]** is diff different work node is is not a  
**[13:46]** part of the uh hierarchy of the uh of  
**[13:49]** the work of the act uh but represents  
**[13:53]** different work and different um um  
**[13:58]** uh different uh uh document legislative  
**[14:01]** document uh inside uh act we you may see  
**[14:07]** parts as a level as a first level  
**[14:09]** dividing uh the the whole tax of the act  
**[14:12]** into big bigger uh parts and um inside  
**[14:18]** each part you may see uh sections and  
**[14:21]** subsections. Uh  
**[14:24]** the interesting part here is that you  
**[14:26]** you may uh notice the cross reference  
**[14:29]** because uh those those are hierarchical  
**[14:32]** uh um ages uh the each each section has  
**[14:37]** subsections and so on representing  
**[14:40]** particular texts but here you have uh uh  
**[14:46]** subsection which refers to another  
**[14:48]** section. So let's say uh in in in that  
**[14:52]** particular law uh somewhere in in in  
**[14:56]** that subsection uh the legislaturator  
**[15:00]** refers to the same text inside the uh  
**[15:03]** inside the document and we represent it  
**[15:07]** this way. So uh we will um explore how  
**[15:11]** how this can help in uh in in the  
**[15:13]** retrieval part. But uh in general this  
**[15:17]** uh a common tosso uh is is uh is helping  
**[15:22]** us to represent law as as it is.  
**[15:27]** Uh the the third layer. So the the uh  
**[15:30]** there are actually um uh three layers if  
**[15:34]** if we talk about um constructing our  
**[15:37]** graph. The the first layer is the graph  
**[15:39]** itself. And we uh we use  
**[15:44]** uh fiber and a common torso to construct  
**[15:48]** our data model and represent hierarchy  
**[15:50]** of of legal documents and and  
**[15:52]** collections of documents and and they  
**[15:55]** their um their combinations.  
**[15:59]** But uh the second the second level  
**[16:01]** definitely is the um vector  
**[16:04]** representations of the of the texts and  
**[16:08]** uh we search uh we use combined search  
**[16:12]** hybrid search by by vector um  
**[16:16]** knowledge by uh graph traversals and  
**[16:20]** also we implemented the classification  
**[16:22]** layer which uh uh helps us a lot to  
**[16:27]** define which particular which text  
**[16:30]** particularly we should search in the uh  
**[16:33]** in our database to extract um context  
**[16:37]** more precisely. Uh uh uh we defined  
**[16:42]** concepts, topics and functional  
**[16:46]** u graphs as as I call it. Um uh most of  
**[16:51]** those uh concepts and topics were  
**[16:53]** extracted by by uh L classification with  
**[16:57]** concept and topics being in enumerated  
**[17:00]** type and functional object being the um  
**[17:04]** uh generated uh text u  
**[17:10]** basing on the on the on the source of  
**[17:13]** the note. Uh so uh we we here follow the  
**[17:17]** rule uh of constructing the graph  
**[17:20]** subject predicate object with the text  
**[17:23]** of each paragraph being u uh being the  
**[17:27]** subject uh the functional role being the  
**[17:30]** the predicate and the functional object  
**[17:33]** being uh the uh real um object real um  
**[17:40]** um matter which uh this role is aimed  
**[17:44]** too. So in in other words we um  
**[17:48]** represent um another layer when when you  
**[17:52]** have when you can have for example uh  
**[17:55]** enabling clause or or definition clause  
**[17:59]** or um represent any other role which uh  
**[18:04]** uh particular paragraph may uh act as in  
**[18:09]** in in the text of the decision of the  
**[18:12]** court decision or the legislative act  
**[18:13]** and on.  
**[18:15]** Uh this is how it it defines in the uh  
**[18:18]** in our database. Um so you can see  
**[18:22]** concept being uh for example delegated  
**[18:24]** legislation legislation topic family  
**[18:27]** law. Uh um this functional role  
**[18:30]** represents uh here enabling clause and  
**[18:33]** the functional object is a [snorts]  
**[18:36]** uh expressing enabling clause minister's  
**[18:38]** authority to amend the the shadow via  
**[18:42]** gazette order. So this uh enabling  
**[18:45]** clause is the  
**[18:47]** role performed by that particular piece  
**[18:49]** of uh of text uh which is represented by  
**[18:54]** the note and the functional object  
**[18:57]** stored in the u in the age uh in in  
**[19:00]** properties of age represents uh to which  
**[19:04]** uh object this role is being applied. Uh  
**[19:07]** this is how it looks like in our uh  
**[19:10]** interface when you uh extract uh  
**[19:15]** knowledge from the uh from the from the  
**[19:19]** knowledge graph. Uh we uh we defined  
**[19:22]** several  
**[19:24]** uh sever several frames. Here you can  
**[19:27]** see the case law representing  
**[19:30]** uh uh four nodes. Each node has issue  
**[19:34]** identific  
**[19:35]** has functional role has topics concepts  
**[19:39]** uh and and functional object as well as  
**[19:43]** content itself for sure. Uh so how it  
**[19:47]** helps us to  
**[19:50]** uh define  
**[19:53]** uh to extract the the context. Uh  
**[19:58]** first of all direct text to cipher  
**[20:00]** retrieval um uh is is is very helpful  
**[20:04]** when you need to extract particular  
**[20:08]** text of the decision or particular um  
**[20:12]** paragraph or particular uh provision of  
**[20:16]** the act. Uh this also helps us uh to  
**[20:20]** extract knowledge using classification  
**[20:24]** layer. Uh for example, if you need to  
**[20:26]** extract some definition, you may uh opt  
**[20:29]** out using uh cipher uh text to cipher  
**[20:33]** procedure avoiding uh any uh vector  
**[20:37]** search. So it's it's it's very fast and  
**[20:41]** points you directly to u um existing uh  
**[20:47]** classification layer nodes. Moreover, if  
**[20:50]** you uh you may you may apply u multiple  
**[20:55]** uh search uh strategy. For example, if  
**[20:59]** you need to extract all the arguments of  
**[21:02]** parties uh in case in case law related  
**[21:07]** to drug trafficking. Uh you may extract  
**[21:11]** this you applying those filters also  
**[21:13]** pretty easily. uh as cipher u  
**[21:18]** queries allows us to do that because uh  
**[21:21]** because we as I said have uh those uh  
**[21:28]** concepts have have these topics and  
**[21:31]** functional roles connected to every  
**[21:34]** every paragraph it's it may be uh  
**[21:37]** relevant to so if you if you're  
**[21:39]** searching for particular concept you  
**[21:42]** will get uh not only one U particular  
**[21:46]** node but also other nodes which which  
**[21:49]** are not directly mentioned in in the  
**[21:53]** vector uh search or in semantic  
**[21:57]** um parts of the of the uh of the graph  
**[22:01]** and so on. So and uh um  
**[22:06]** this uh this is the use of  
**[22:08]** classification layer. Uh as I as I uh  
**[22:12]** said um you may see here that um in in  
**[22:16]** in function in those classification  
**[22:18]** layer nodes we we have also embedded  
**[22:21]** which allows us to um uh make index  
**[22:26]** indexing and search uh on that on those  
**[22:29]** objects. So in other words, if I if I'm  
**[22:31]** searching something related to family  
**[22:34]** law, uh I I shouldn't have to uh I don't  
**[22:38]** don't necessarily have to use family law  
**[22:41]** to to construct the uh cipher um query,  
**[22:47]** but may may use different approaches to  
**[22:50]** to wording and uh that that provides  
**[22:54]** super flexibility in uh when uh uh  
**[22:58]** extracting  
**[22:59]** knowledge from classification layer. uh  
**[23:03]** for sure vectors uh find semantic  
**[23:06]** candidates and and and provide those to  
**[23:09]** uh uh LLM uh context uh uh and those  
**[23:15]** those three layers can can work  
**[23:17]** independently uh where if you if you  
**[23:20]** want to grab uh some particular uh  
**[23:23]** paragraph of particular decision you you  
**[23:26]** go and use uh direct cipher. If you want  
**[23:30]** to extract some knowledge, some um um  
**[23:36]** definitions or uh any any kind of  
**[23:39]** classifications,  
**[23:41]** uh you may use both direct cipher uh  
**[23:45]** unclassification layer and vector search  
**[23:47]** on classification layer or you may uh  
**[23:51]** use classical LM approach uh extracting  
**[23:55]** knowledge from uh semantic  
**[23:59]** uh semantic layer using uh vector  
**[24:03]** search. But uh combining those together  
**[24:06]** allows us to  
**[24:08]** get very very flexible results and uh  
**[24:13]** make double double uh check on the  
**[24:17]** consistency of the contacts providing to  
**[24:19]** the LLM. Um  
**[24:22]** for sure graph traversal expands the  
**[24:25]** neighborhood that that is important  
**[24:27]** because um uh at some points um it's not  
**[24:32]** only uh the particular paragraph found  
**[24:35]** as as a semantic candidate. uh it it  
**[24:38]** doesn't explain uh in details  
**[24:42]** uh the the whole semantic especially if  
**[24:45]** it refers to other um uh paragraph other  
**[24:50]** pro text provision uh other uh law  
**[24:54]** provision and so on. So in other words,  
**[24:56]** if the if the judge mentions some uh  
**[24:58]** decision, some decision or or statutes  
**[25:01]** or or precedents in in its text, uh this  
**[25:05]** particular paragraph cannot only be the  
**[25:09]** the sole text provided to LLM.  
**[25:12]** It it should be accompanied by its  
**[25:14]** neighborhood and especially those those  
**[25:18]** texts and and  
**[25:21]** paragraphs and status refer referenced  
**[25:24]** in that initial semantic candidate. Uh  
**[25:29]** this is definitely uh uh how lawyers  
**[25:32]** work when they when they define the uh  
**[25:36]** the applicable law. When they when they  
**[25:37]** found some uh important provisions in or  
**[25:40]** or usable um text in in the court  
**[25:43]** decision, they referencing to another uh  
**[25:47]** status or or provision. they definitely  
**[25:49]** should uh uh go and and see what's  
**[25:52]** what's saying in that uh particular uh  
**[25:56]** piece of text reference. Uh so it allows  
**[26:00]** us also to to calculate missing events  
**[26:02]** uh when you when you can extract uh uh  
**[26:06]** what is um what was not what was not  
**[26:09]** covered by the context or extract some  
**[26:12]** knowledge from uh some insights from u u  
**[26:18]** from a user query uh which which can be  
**[26:21]** missing. For example, if the uh if the  
**[26:24]** user provides uh information about it  
**[26:27]** case his case uh he may not be providing  
**[26:32]** some important details and using data  
**[26:35]** model uh and those uh combined approach  
**[26:38]** we may extract and define which  
**[26:42]** information is missing. Uh and also this  
**[26:45]** all this uh uh is is a very human in the  
**[26:48]** loop in react friendly. Uh we can uh  
**[26:51]** interrupt uh the the proceding at any  
**[26:53]** time uh suggest user to uh to uh  
**[26:58]** coordinate the next actions and or using  
**[27:02]** all those three um uh layers uh as a  
**[27:06]** tools in React uh agents. Uh so uh  
**[27:12]** here's here's the um here's a big  
**[27:14]** picture of how two case law note can be  
**[27:19]** connected to each other comparing with  
**[27:21]** the with the act. Uh sorry I will  
**[27:24]** briefly leave it here and uh uh  
**[27:29]** we'll allow to ask some questions if you  
**[27:32]** have uh please feel free  
**[27:42]** I see uh yes I see the the question uh  
**[27:46]** asking me can can you have record  
**[27:48]** scoring based uh on numbers uh of  
**[27:53]** entities or another logic. Uh for sure  
**[27:56]** we we  
**[27:58]** um um uh we arrange uh results as  
**[28:05]** the uh here here's the here's example of  
**[28:09]** how the contact look like. Uh you may  
**[28:12]** see the uh the question and the answer  
**[28:16]** uh of particular of particular  
**[28:20]** um for example this way. Here's the  
**[28:24]** question and the answer. And this one is  
**[28:26]** context. And this one beautiful is the  
**[28:30]** is the graph we constructed out of those  
**[28:34]** uh nodes. Uh so as you can see we we  
**[28:39]** have here all the uh extraive nodes with  
**[28:44]** legal interpret with the functional rows  
**[28:48]** legal topics and so on. And each  
**[28:50]** paragraph is is represented by the by  
**[28:54]** the simplified content uh and so on.  
**[28:58]** Also we have some uh acts and may refers  
**[29:03]** to and those uh links also refer to  
**[29:07]** particular nodes in the graph. U so  
**[29:11]** that's that's in general the the whole  
**[29:13]** picture of uh how the service works. Uh  
**[29:17]** please provide the questions if you have  
**[29:18]** it.  
**[29:50]** Uh yes, there's a there's a some  
**[29:53]** drawbacks here. Uh and I didn't explain  
**[29:56]** it probably. uh not not drawbacks but uh  
**[30:00]** um  
**[30:02]** uh  
**[30:06]** but some uh let's say u uh problems  
**[30:10]** challenges on the way we uh we should  
**[30:13]** focus on uh we may take a look at those  
**[30:16]** closely um those are can be  
**[30:20]** first of all the problems of with  
**[30:23]** classification it it cannot be for sure  
**[30:27]** uh guaranteed that uh uh classification  
**[30:30]** is correct. The other is the is the uh  
**[30:35]** different  
**[30:37]** formats of documents used by the uh by  
**[30:40]** users or or different  
**[30:45]** models of uh legislation. This that that  
**[30:48]** is particular problem where uh Eurolex  
**[30:52]** European uh publishing office struggling  
**[30:55]** uh applying the um a common tosso and  
**[31:00]** the uh developing their knowledge graph  
**[31:03]** because the as you may know um  
**[31:08]** the  
**[31:10]** legislative field of European Union is  
**[31:12]** very fracted. uh it it consists of 27  
**[31:16]** countries and each country has its uh  
**[31:19]** local legisl legislation it's local  
**[31:23]** rules  
**[31:24]** it's tradition language and so on and on  
**[31:28]** top of that exist the the layer of  
**[31:32]** legislative layer of and uh litigation  
**[31:36]** layer of uh of of European Union. So  
**[31:39]** combining all these together is is  
**[31:41]** pretty challenging and applying  
**[31:44]** um  
**[31:45]** exact um knowledge graphs to to those uh  
**[31:51]** uh fragmentated pieces of legislation is  
**[31:54]** is super inconvenient. So that is the  
**[31:58]** one of the major problems here. Uh  
**[32:02]** others um  
**[32:05]** there are actually many many problems  
**[32:07]** here. Here we are ch we are tackling the  
**[32:10]** the other is extracting references  
**[32:13]** because judges in their decisions always  
**[32:17]** or in most cases use like anchors saying  
**[32:21]** that this uh this act referencing to  
**[32:24]** another act or another court decision.  
**[32:27]** uh mention that first time in their text  
**[32:30]** and then using some abbreviation or some  
**[32:34]** um reference to that anchor uh place it  
**[32:37]** in in the beginning of the text and and  
**[32:39]** if you take particular text of the  
**[32:43]** paragraph and try to extract the know  
**[32:45]** the reference to uh that uh anchor it's  
**[32:49]** it's pretty uh pretty difficult to  
**[32:51]** perform. you have to insert some  
**[32:55]** temporary anchor to to get the uh  
**[33:01]** correct uh reference. Uh so many many  
**[33:05]** many many problems but but the uh uh but  
**[33:09]** the solution is very promising because  
**[33:10]** we saw how uh how convenient and how  
**[33:14]** flexible is the uh uh is the extraction  
**[33:18]** extraction u uh workflow and uh we see  
**[33:23]** the real u results in benchmarking with  
**[33:28]** the existing uh um assistance and use  
**[33:33]** for our uh retrieval parts for different  
**[33:37]** workflows like uh combining the the  
**[33:40]** knowledge or combining the um contacts  
**[33:44]** for particular  
**[33:48]** uh particular query.  
**[33:52]** So uh  
**[33:57]** question how many times you deleted your  
**[33:59]** database before you get it right. Um  
**[34:02]** actually um uh we we we never delete it.  
**[34:07]** We just make it right one time. Uh  
**[34:10]** and uh but we roll rolled back several  
**[34:14]** times to  
**[34:16]** to the uh eliminating the made progress.  
**[34:25]** Uh so I guess we don't have much  
**[34:29]** questions. uh may the we may end the  
**[34:34]** session. Uh if anybody has any any other  
**[34:39]** question that's the last chance to ask.  
**[34:43]** uh we benchmarking uh  
**[34:46]** on each stage of of u um major step  
**[34:51]** towards the  
**[34:53]** uh there's a question on on benchmarking  
**[34:56]** uh post creation uh uh or uh on on the  
**[35:00]** fly. Yes, we uh we are making uh since  
**[35:03]** we got the uh working u  
**[35:08]** zero version of the database and and  
**[35:11]** retrieval part we try to extract uh and  
**[35:15]** compare the results with the  
**[35:17]** >> [snorts]  
**[35:17]** >> uh other uh assistance and uh it allows  
**[35:22]** us to compare the results.  
**[35:26]** >> All right, thank you so much for all  
**[35:28]** your questions. We are at time and  
**[35:34]** attend their next session. Thank you so  
**[35:36]** much for joining  
**[35:40]** >> Sal we can we can hear you. Okay. Um  
**[35:44]** >> just jumping in. Um Alex over here I  
**[35:47]** think there's some network issue with  
**[35:48]** Salah. Um thank you so much for your  
**[35:52]** talk. Um we'll be ending this one.  
**[35:54]** Thanks a lot and we'll go on to the  
**[35:56]** next.  
**[35:57]** >> Thank you ma'am.  
**[35:58]** >> Bye. Take care.  
**[36:02]** [music]  