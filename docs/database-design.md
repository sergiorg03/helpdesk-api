# Database Design

## 1. Overview

The HelpDesk API database is designed to manage technical support tickets, user accounts, comments and ticket activity history.

The database will use **PostgreSQL** as its relational database management system.

All entities will use UUIDs as primary keys to provide unique identifiers without relying on sequential values.

## 2. Database Entities

The initial database schema consists of four main entities:

- **Users:** Stores user accounts and their roles.
- **Tickets:** Stores support tickets and their current information.
- **Comments:** Stores messages associated with support tickets.
- **TicketHistory:** Records changes and events related to support tickets.

## 3. Entity Definitions

### 3.1 Users

Stores information about registered users.

| Field           | Data Type    | Constraints      |
| --------------- | ------------ | ---------------- |
| id              | UUID         | Primary Key      |
| username        | VARCHAR(50)  | Unique, Not Null |
| email           | VARCHAR(255) | Unique, Not Null |
| hashed_password | VARCHAR(255) | Not Null         |
| role            | VARCHAR(20)  | Not Null         |
| is_active       | BOOLEAN      | Not Null         |
| created_at      | TIMESTAMPTZ  | Not Null         |

**User roles:**

- `ADMIN`: Manages users and the entire support system.
- `TECHNICIAN`: Handles and resolves assigned tickets.
- `CUSTOMER`: Creates tickets and communicates with technicians.

### 3.2 Tickets

Stores support tickets created by customers.

| Field          | Data Type    | Constraints                      |
| -------------- | ------------ | -------------------------------- |
| id             | UUID         | Primary Key                      |
| title          | VARCHAR(150) | Not Null                         |
| description    | TEXT         | Not Null                         |
| status         | VARCHAR(20)  | Not Null                         |
| priority       | VARCHAR(20)  | Not Null                         |
| created_by_id  | UUID         | Foreign Key → Users.id, Not Null |
| assigned_to_id | UUID         | Foreign Key → Users.id, Nullable |
| created_at     | TIMESTAMPTZ  | Not Null                         |
| updated_at     | TIMESTAMPTZ  | Not Null                         |
| closed_at      | TIMESTAMPTZ  | Nullable                         |

**Ticket statuses:**

- `OPEN`: Newly created ticket.
- `IN_PROGRESS`: Ticket currently being handled.
- `PENDING`: Waiting for additional information or action.
- `CLOSED`: Resolved or closed ticket.

**Ticket priorities:**

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Each ticket can be assigned to a maximum of one technician. The `assigned_to_id` field remains nullable until a technician is assigned.

### 3.3 Comments

Stores messages exchanged between customers, technicians and administrators within a ticket.

| Field      | Data Type   | Constraints                        |
| ---------- | ----------- | ---------------------------------- |
| id         | UUID        | Primary Key                        |
| ticket_id  | UUID        | Foreign Key → Tickets.id, Not Null |
| author_id  | UUID        | Foreign Key → Users.id, Not Null   |
| content    | TEXT        | Not Null                           |
| created_at | TIMESTAMPTZ | Not Null                           |

Each comment belongs to one ticket and is written by one user.

### 3.4 TicketHistory

Stores the history of changes and events associated with each ticket.

| Field      | Data Type   | Constraints                        |
| ---------- | ----------- | ---------------------------------- |
| id         | UUID        | Primary Key                        |
| ticket_id  | UUID        | Foreign Key → Tickets.id, Not Null |
| actor_id   | UUID        | Foreign Key → Users.id, Not Null   |
| event_type | VARCHAR(50) | Not Null                           |
| old_value  | TEXT        | Nullable                           |
| new_value  | TEXT        | Nullable                           |
| created_at | TIMESTAMPTZ | Not Null                           |

This entity allows the application to track events such as:

- Ticket creation.
- Status changes.
- Priority changes.
- Technician assignments.
- Ticket closure.

History records should be immutable through the normal application API to preserve an accurate audit trail.

## 4. Entity Relationships

The database will follow these relationships:

| Relationship             | Type        | Description                                    |
| ------------------------ | ----------- | ---------------------------------------------- |
| Users → Tickets          | One-to-Many | A user can create multiple tickets.            |
| Users → Assigned Tickets | One-to-Many | A technician can be assigned multiple tickets. |
| Tickets → Comments       | One-to-Many | A ticket can contain multiple comments.        |
| Users → Comments         | One-to-Many | A user can write multiple comments.            |
| Tickets → TicketHistory  | One-to-Many | A ticket can have multiple history records.    |
| Users → TicketHistory    | One-to-Many | A user can generate multiple history events.   |

## 5. Database Design Decisions

- **UUID primary keys:** All entities use UUIDs instead of sequential integer identifiers.
- **Single technician assignment:** Each ticket can have only one assigned technician at a time.
- **Nullable technician assignment:** Tickets can exist without an assigned technician.
- **Audit history:** Ticket changes are recorded in a separate table.
- **Timestamps:** Creation and modification dates are stored using `TIMESTAMPTZ`.
- **Password security:** Passwords are stored as secure hashes, never as plain text.
- **Referential integrity:** Foreign keys maintain relationships between entities.

## 6. Future Improvements

The database schema may be extended with additional functionality as the project evolves:

- File attachments for tickets.
- Internal notes for technicians.
- Email notification records.
- Ticket categories and tags.
- Advanced reporting and statistics.
