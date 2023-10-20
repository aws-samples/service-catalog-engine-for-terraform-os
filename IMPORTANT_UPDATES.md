## [10/20/2023] Migration from `TERRAFORM_OPEN_SOURCE` to `EXTERNAL` product type
AWS Service Catalog plans on introducing some important changes to their support of Terraform Open Source starting October 12, 2023. If you are not already aware, HashiCorp announced a switch from the Mozilla Public License (MPL) 2.0 to the Business Source License for Terraform. This change impacts customers who are using Terraform Open Source with Service Catalog, because references to 'open source' will be changed. Currently, Service Catalog references ‘open-source’ language in various artifacts such as our APIs, console, documentation, and a publicly available reference engine (TRE) that can be accessed through GitHub.

Because of these changes, the following dates and action items should be noted:
* **October 12, 2023** – Service Catalog will introduce a new parameter input for `ProductType` and `ProvisionedProductType` which will impact public APIs such as CreateProduct, UpdateProduct, DescribeRecord and more. The new input parameter will be `EXTERNAL` which will introduce a non-breaking change to both API, CLI, and console experiences. The `EXTERNAL` product type can be used by customers for 3rd party reference engines including the existing "Terraform Open Source" (now referred to as Terraform Community), Pulumi, Puppet, Chef, and more. The `EXTERNAL` product type is intended to replace the `TERRAFORM_OPEN_SOURCE` product type.
* **December 14, 2023** – Service Catalog will prevent the creation of new product types and provisioned products with the type `TERRAFORM_OPEN_SOURCE`. Customers are also encouraged to upgrade their reference engines which will prevent them from using a distribution of Terraform that is no longer supported. Note, that existing resources (i.e., versions, existing provisioned products) of type `TERRAFORM_ OPEN_SOURCE` can still be updated or terminated.

Between October 12, 2023 to December 14, 2023, customers are encouraged to take the following actions:
1. Upgrade your existing Terraform Reference Engine for AWS Service Catalog to include support for both the new `EXTERNAL` and previous `TERRAFORM_OPEN SOURCE` product types.
1. Recreate the existing products using the new `EXTERNAL` product type.
1. Delete any existing products that use the `TERRAFORM_OPEN_SOURCE` product type.
1. Reprovision (or relaunch) those resources using the new `EXTERNAL` product type.
1. Terminate any existing provisioned products that use the `TERRAFORM_OPEN_SOURCE` product type.
1. Any new products and launched provisioned resources should reference the `EXTERNAL` product type.
