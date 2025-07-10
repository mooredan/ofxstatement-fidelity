# Fidelity CSV plugin for ofxstatement

This project is a plugin for [ofxstatement](https://github.com/kedder/ofxstatement)
that will process a CSV file of investment account transaction history from Fidelity
and convert it to OFX format, suitable for importing into GnuCash.

## Running

Use `pipenv` to run the converter:

```
$ pip3 install pipenv --user (if it hasn't already been set up)
$ cd ofxstatement-fidelity
$ pipenv sync --dev
$ pipenv shell
$ ofxstatement convert -t fidelity Name_XXX321_Transactions_20240101-123456.json import.ofx
```

## Known Limitations

### Splits, Spin-offs

Fidelity doesn't provide ratio information for stock splits which is required for
the OFX `<SPLIT>` element.
Nor does GnuCash support importing the OFX `<SPLIT>` element.
So that you at least get some information imported,
these generate `<TRANSFER>` transactions and a warning message to remind you
that you'll likely want to manually update these transactions depending on
how you choose to track splits and their cost basis.

One approach for tracking splits in GnuCash is to change the import transaction
to reverse out the existing lots and their remaining cost bases,
and add back in the new total shares with a corresponding buy cost.

For example, a 4:1 split on 100 shares would be imported as a net 300 share transfer.
Change that transaction to be:
* -100 shares at a sale price of the remaining cost basis
* +400 shares at a buy price of the remaining cost basis

The date won't be correct for calculating the long-term capital gain tax implications,
but at least the per-share gain calculations should be correct.

## Setting up development environment

Use `pipenv` to make a clean development environment.

```
$ cd ofxstatement-fidelity
$ pipenv sync --dev
```

This will download all the dependencies and install them into your virtual
environment. To enter the development environment:

```
$ pipenv shell
```

Inside the `pipenv` shell:

```
$ ofxstatement list-plugins
The following plugins are available:

  fidelity      Parses Fidelity CSV export of investment transactions
```

Alternatively, single commands can be run inside the `pipenv` environment
directly from the main shell:

```
$ pipenv run ofxstatement list-plugins
```

### Upgrading Dependencies

After running `pipenv shell`, run `pipenv update` to update everything.

### Testing

Run the following command to run the test suite, type checks, and text
formatting (see [Makefile](Makefile) for details):

```
$ pipenv run make all
```

## Packaging

```
$ python -m build
```

## References

* [OFX specification](https://financialdataexchange.org/common/Uploaded%20files/OFX%20files/OFX%20Banking%20Specification%20v2.3.pdf)
* [GnuCash OFX code](https://github.com/Gnucash/gnucash/blob/stable/gnucash/import-export/ofx/gnc-ofx-import.cppx)
* [libofx](https://github.com/libofx/libofx)
