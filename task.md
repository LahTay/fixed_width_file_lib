The task:
1. Implement a small library that allows you to write and read files of fixed-width format. The file
structure is described in the table below.
2. Write an application with a CLI interface that provides the following possibilities:
- get the value of any field
- change field values
- add transactions (for transaction definition - read the second page)

Nice to have:
- A possibility to close some fields for changes
- Validation of the file structure
- Production-like error handling mechanism
- Properly implemented logging according to python logging cookbook
- Tests

General requirements:
- It is important how you organize the project.
- The code must be first - readable, second - reliable, and third - fast. In that exact order of
importance.
- Pay attention to the type of data used to present financial information.
Code should be provided in an archive, uploaded to the google drive. The link should be shared
with interviewers.

The file has a fixed width structure and consists of records of different types. Length of each line
is 120 symbols. Each record is delimited by a line ending symbol, which should be OS-agnostic.
Unused space is padded at the left by whitespaces.
Schematized structure of the file (all lines are placed in the strict order):
1 Header (mandatory)
2 Transaction (can be repeated from 1 to 20000 times)
3 Footer (mandatory)

### **Fixed-Width File Structure**

| **Record Type** | **Position (From-To)** | **Data Type** | **Field Name** | **Extra Info**                                                      |
|-----------------|------------------------|---------------|----------------|---------------------------------------------------------------------|
| Header          | 1-2                    | String        | Field ID       | Fixed value `"01"`                                                  |
|                 | 3-30                   | String        | Name           |                                                                     |
|                 | 31-60                  | String        | Surname        |                                                                     |
|                 | 61-90                  | String        | Patronymic     |                                                                     |
|                 | 91-120                 | String        | Address        |                                                                     |
| Transaction     | 1-2                    | String        | Field ID       | Fixed value `"02"`                                                  |
|                 | 3-8                    | String        | Counter        | Format: `000001 - 020000` (incremented automatically)               |
|                 | 9-20                   | Number        | Amount         | Format: `000000002000` (last two digits are decimal, leading zeros) |
|                 | 21-23                  | String        | Currency       | Fixed list of possible values                                       |
|                 | 24-120                 | String        | Reserved       | Spaces                                                              |
| Footer          | 1-2                    | String        | Field ID       | Fixed value `"03"`                                                  |
|                 | 3-8                    | Number        | Total Counter  | Format: `000001 - 020000` (total transaction count)                 |
|                 | 9-20                   | Number        | Control Sum    | Format: `000000002000` (sum of all transactions)                    |
|                 | 21-120                 | String        | Reserved       | Spaces                                                              |
