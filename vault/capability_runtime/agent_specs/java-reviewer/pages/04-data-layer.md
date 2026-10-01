### HIGH -- JPA / Relational Database
- **N+1 query problem**: `FetchType.EAGER` on collections — use `JOIN FETCH` or `@EntityGraph` / `@NamedEntityGraph`
- **Unbounded list endpoints**:
  - **[SPRING]**: Returning `List<T>` without `Pageable` and `Page<T>`
  - **[QUARKUS]**: Returning `List<T>` without `PanacheQuery.page(Page.of(...))`
- **Missing `@Modifying`**: Any `@Query` that mutates data requires `@Modifying` + `@Transactional`
- **Dangerous cascade**: `CascadeType.ALL` with `orphanRemoval = true` — confirm intent is deliberate
- **[QUARKUS] Active record misuse**: Mixing `PanacheEntity` and `PanacheRepository` in the same bounded context — pick one and stay consistent

### HIGH -- Panache MongoDB [QUARKUS only]
- **Missing codec or serialisation config**: Custom types in documents without a registered `Codec` or proper BSON annotation — causes silent serialisation failures
- **Unbounded `listAll()` / `findAll()`**: Using `PanacheMongoEntity.listAll()` or `PanacheMongoRepository.listAll()` without pagination — use `.find(query).page(Page.of(index, size))`
- **No index on query fields**: Querying by fields not covered by a MongoDB index — define indexes via `@MongoEntity(collection = "...")` + migration scripts or `createIndex()` at startup
- **ObjectId vs custom ID confusion**: Using `String` id fields without explicit `@BsonId` or `@MongoEntity` configuration — leads to `_id` mapping issues; prefer `ObjectId` or document the custom ID strategy
- **Blocking MongoDB client on reactive thread**: Using the classic `MongoClient` (blocking) in a reactive pipeline — use `ReactiveMongoClient` and return `Uni<T>` / `Multi<T>`
- **Active record misuse**: Mixing `PanacheMongoEntity` and `PanacheMongoRepository` in the same bounded context — pick one and stay consistent
- **Missing `@Transactional` awareness**: MongoDB multi-document transactions require an explicit `ClientSession` — Panache MongoDB does not auto-manage transactions like Hibernate ORM; document the consistency guarantees

### MEDIUM -- NoSQL General
- **Schema evolution without migration strategy**: Changing document shapes without a versioned migration plan (e.g. a `schemaVersion` field or migration script) — leads to runtime deserialization failures on old documents
- **Storing large blobs in documents**: Embedding large binary data directly in documents instead of using GridFS or external storage — causes memory pressure and hits the 16 MB BSON limit
- **Overly nested documents**: Deeply nested document structures that should be modelled as separate collections with references — query and update complexity grows exponentially
- **Missing TTL or expiry policy**: Time-sensitive data (sessions, tokens, caches) stored without a TTL index — leads to unbounded collection growth
- **No read preference / write concern configuration**: Production deployments using defaults without evaluating consistency requirements

