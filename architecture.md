## Deployment description

Various possible deployments configurations of PeARS combined with On My Disk are described below.

### Integrated on onmydisk.net

In this deployment PeARS is hosted along the server side component of On My Disk.

```mermaid
    C4Context
      title Integrated on onmydisk.net
      Boundary(pears-omd-integration, "PeARS - On My Disk integration") {
        Person(user, "End user")
      
        Boundary(b1, "End user computer") {
      
          System(storage, "Personal storage", "E.g. a computer hard drive.")
      
          System(omd-desktop-client, "On My Disk desktop client", "Indexes files")
        }
      
        Boundary(b2, "onmydisk.net") {
          System(omd-server, "On MyDisk server", "Indexes files content")
          System(pears, "PeARS")
        }
      }
      
      Rel(user, storage, "Store files")
      Rel(omd-desktop-client, storage, "Accesses and indexes files")
      BiRel(omd-server, omd-desktop-client, "Uses to access files content")
      Rel(pears, omd-server, "Get content indexes - delegate user auth")
      Rel(omd-server, pears, "Delegate search feature")

      UpdateRelStyle(omd-server, pears, $textColor="red", $offsetY="00")

```
